import json
import paho.mqtt.client as client
from typing import Any, Callable
from dataclass_type_validator import TypeValidationError

from .protocol import MsgMethods, MsgRequest
from .task import TaskForApp, TaskStatus, TaskExitCode
from .mqtt import FunctionCallerMqttEndPoint
from .generic import Output as _


class FunctionCallerApp(FunctionCallerMqttEndPoint):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.functions = {"hello": lambda value: value + " hello!"}
        self.tasks: list[TaskForApp] = []

    def add(self, function_name: str) -> Callable[[Any], None]:
        self.prevent_is_not_running()
        if self.functions.get(function_name):
            raise NameError(f"Function with this name '{function_name}' already exists.")

        def inner(func):
            self.functions[function_name] = func
            return func
        return inner

    def handle_mqtt_message(self, client: client.Client, userdata: Any, msg: client.MQTTMessage) -> None:
        # decode message data to json dict object
        requests_data: dict
        try: request_data = json.loads(msg.payload.decode("utf-8"))
        except json.decoder.JSONDecodeError: return

        # check types and content inside json
        request: MsgRequest
        try: request = MsgRequest(**request_data)
        except TypeValidationError:
            task_id = request_data.get(MsgRequest.alias.ID)
            if task_id and isinstance(task_id, str):
                self.tasks.append(TaskForApp.create_completed_task(task_id, TaskExitCode.BAD_REQUEST))
            return

        # check if function exists
        function = self.functions.get(request.function_name)
        if not function:
            self.tasks.append(TaskForApp.create_completed_task(request.id, TaskExitCode.FUNCTION_NOT_FOUND))
            return

        # create actual task
        self.tasks.append(
            TaskForApp(
                id=request.id,
                function=function,
                function_name=request.function_name,
                function_kwargs=request.function_kwargs,
            )
        )

    def publish_completed_tasks(self):
        for task in TaskForApp.filter(self.tasks, status=TaskStatus.COMPLETED):
            json_response = task.to_response().to_json()
            self.client.publish(topic=MsgMethods.RESPONSE.value, payload=json_response)
            self.tasks.remove(task)

    def exec_tasks_in_order(self):
        for task in TaskForApp.filter(self.tasks, status=TaskStatus.IN_ORDER):
            task.exec_function_in_thread()

    def handle_mqtt_connect(self, *args, **kwargs) -> None:
        super().handle_mqtt_connect(*args, **kwargs)
        self.client.subscribe(MsgMethods.REQUEST.value, qos=self.MQTT_QOS)

    def loop(self):
        super().loop()
        self.exec_tasks_in_order()
        self.publish_completed_tasks()


if __name__ == "__main__":
    app = FunctionCallerApp(
        mqtt_url="362a5de461ca4a79858f8b50eb805cd8.s1.eu.hivemq.cloud",
        mqtt_port=8883,
        mqtt_username="FunctionCaller",
        mqtt_password="Wx)8Yw^7bCNDr,V",
    )

    @app.add("sub")
    def sub(a: int, b: int) -> _:
        return _(a + b)

    app.run(run_in_thread=True)
