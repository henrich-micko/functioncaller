from enum import Enum
from typing import Any, Callable, Union, Iterable
from threading import Thread

from .utils import generate_char_code
from .protocol import MsgRequest, MsgResponse
from .generic import Output


class TaskStatus(Enum):
    IN_ORDER = 0
    IN_PROGRESS = 1
    COMPLETED = 2


class TaskExitCode(Enum):
    SUCCESS = 0
    ERROR = 1
    BAD_REQUEST = 2
    FUNCTION_NOT_FOUND = 3
    BAD_RESPONSE = 4


class BaseTask:
    ID_LENGTH = 10

    def __init__(self, function_name: str, function_kwargs: dict, id: str = None,
                 status: TaskStatus = TaskStatus.IN_ORDER, exit_code: Union[TaskExitCode, None] = None) -> None:

        self.id = id if id is not None else BaseTask.generate_task_id()
        self.function_name = function_name
        self.function_kwargs = function_kwargs
        self.status = status
        self.exit_code = exit_code

        self.output = Output()

    def __str__(self) -> str:
        return self.id

    @property
    def is_complete(self):
        return self.status is TaskStatus.COMPLETED

    @classmethod
    def filter(cls: "BaseTask", array: Iterable["BaseTask"], **kwargs: dict[str: Any]) -> list[__qualname__]:
        # return all with same kwargs

        def is_valid(item: BaseTask) -> bool:
            for key, value in kwargs.items():
                try:
                    item_attr_value = getattr(item, key)
                    if item_attr_value != value: return False
                except AttributeError: return False
            return True
        return list(filter(is_valid, array))

    @classmethod
    def get(cls: "BaseTask", array: Iterable["BaseTask"], __default: Any = None, **kwargs: dict[str: Any]) -> __qualname__:
        # Return first task with same kwargs

        for task in array:
            for key, value in kwargs.items():
                try: task_attr_value = getattr(task, key)
                except AttributeError: break
                if task_attr_value != value: break
            else: return task
        return __default

    @classmethod
    def generate_task_id(cls) -> str:
        return generate_char_code(cls.ID_LENGTH)


class TaskForApp(BaseTask):
    def __init__(self, *args, function: Union[Callable, None], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.function = function

    def exec_function_in_thread(self) -> None:
        Thread(target=self.exec_function).start()

    def exec_function(self) -> None:
        if not self.status == TaskStatus.IN_ORDER or not callable(self.function):
            return
        self.status = TaskStatus.IN_PROGRESS

        try:
            self.output = self.function(**self.function_kwargs)
            if not isinstance(self.output, Output):
                self.output = Output(self.output)
            self.exit_code = TaskExitCode.SUCCESS
        except BaseException as error:
            self.output = Output(str(error))
            self.exit_code = TaskExitCode.ERROR

        self.status = TaskStatus.COMPLETED

    def to_response(self) -> MsgResponse:
        return MsgResponse(
            id=self.id,
            status=self.status,
            output=self.output,
            exit_code=self.exit_code
        )

    @classmethod
    def create_completed_task(cls: "TaskForApp", task_id: str, exit_code: TaskExitCode) -> __qualname__:
        return TaskForApp(
            id=task_id,
            function=None,
            function_name="",
            function_kwargs={},
            status=TaskStatus.COMPLETED,
            exit_code=exit_code,
        )


class TaskClient(BaseTask):
    def __init__(self, *args, on_complete: Union[Callable, None], **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.on_complete = on_complete

    def to_request(self) -> MsgRequest:
        return MsgRequest(
            id=self.id,
            function_name=self.function_name,
            function_kwargs=self.function_kwargs
        )

    def process_response(self, response: MsgResponse) -> None:
        self.status = TaskStatus(response.status)
        self.exit_code = TaskExitCode(response.exit_code)
        self.output = response.output

        self.if_exists_call_on_complete()

    def process_invalid_response(self) -> None:
        self.status = TaskStatus.COMPLETED
        self.exit_code = TaskExitCode.BAD_RESPONSE

        self.if_exists_call_on_complete()

    def if_exists_call_on_complete(self):
        if self.on_complete and callable(self.on_complete):
            self.on_complete(exit_code=self.exit_code, output=self.output)


class TaskClientPromise:
    TASK_EXIT_CODE_SUCCESSFUL = [
        TaskExitCode.SUCCESS,
    ]

    TASK_EXIT_CODE_FAIL = [
        TaskExitCode.ERROR,
        TaskExitCode.BAD_RESPONSE,
        TaskExitCode.BAD_REQUEST,
        TaskExitCode.FUNCTION_NOT_FOUND,
    ]

    def __init__(self, then: Union[Callable, None] = None, catch: Union[Callable, None] = None):
        self.then_listener = then
        self.catch_listener = catch

    def on_complete(self, exit_code: TaskExitCode, output: Any) -> None:
        if exit_code in self.TASK_EXIT_CODE_SUCCESSFUL and callable(self.then_listener):
            self.then_listener(output=output)

        elif exit_code in self.TASK_EXIT_CODE_FAIL and callable(self.catch_listener):
            self.catch_listener(exit_code=exit_code, output=output)

    # set then
    def then(self, then: Callable):
        self.then_listener = then
        return self

    # set cath
    def catch(self, catch: Callable):
        self.catch_listener = catch
        return self
