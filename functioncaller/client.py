import paho.mqtt.client as client
import json
from typing import Any, Callable
from dataclass_type_validator import TypeValidationError

from .mqtt import FunctionCallerMqttEndPoint
from .task import TaskClient, TaskStatus, TaskClientPromise
from .protocol import MsgMethods, MsgResponse


class FunctionCaller:
    def __init__(self, call_function: Callable) -> None:
        self.call_function = call_function

    def __getattr__(self, name: str) -> Callable:
        def wrapper(**kwargs: Any) -> TaskClientPromise:
            return self.call_function(name=name, **kwargs)
        return wrapper

    @staticmethod
    def from_client(client: "FunctionCallerClient") -> "FunctionCaller":
        return FunctionCaller(call_function=client.call_function)


class FunctionCallerClient(FunctionCallerMqttEndPoint):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tasks: list[TaskClient] = []

    def handle_mqtt_connect(self, *args, **kwargs) -> None:
        super().handle_mqtt_connect(*args, **kwargs)
        self.client.subscribe(MsgMethods.RESPONSE.value, qos=self.MQTT_QOS)

    def call_function(self, name, **function_kwargs) -> TaskClientPromise:
        promise = TaskClientPromise()
        self.tasks.append(
            TaskClient(
                function_name=name,
                function_kwargs=function_kwargs,
                on_complete=promise.on_complete)
        )
        return promise

    def publish_tasks_in_order(self):
        for task in TaskClient.filter(self.tasks, status=TaskStatus.IN_ORDER):
            json_request = task.to_request().to_json()

            self.client.publish(
                topic=MsgMethods.REQUEST.value,
                payload=json_request,
                qos=self.MQTT_QOS,
            )

            task.status = TaskStatus.IN_PROGRESS

    def handle_mqtt_message(self, client: client.Client, userdata: Any, msg: client.MQTTMessage) -> None:
        # parse json message to dict
        response_data: dict
        try: response_data = json.loads(msg.payload.decode("utf-8"))
        except json.decoder.JSONDecodeError: return

        # dict to MsgResponse (check types)
        response: MsgResponse
        try: response = MsgResponse(**response_data)
        except TypeValidationError:
            task_id = response_data.get(MsgResponse.alias.ID)
            if task_id and isinstance(task_id, str):
                task = TaskClient.get(self.tasks, id=task_id)
                if task:
                    task.process_invalid_response()
                    self.tasks.remove(task)
            return

        # process valid response
        task = TaskClient.get(self.tasks, id=response.id)
        if task is None: return

        task.process_response(response)

        self.tasks.remove(task)

    def loop(self):
        self.publish_tasks_in_order()

    def get_caller(self) -> FunctionCaller:
        return FunctionCaller.from_client(client=self)

