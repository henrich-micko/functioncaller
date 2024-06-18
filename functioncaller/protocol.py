import json
from enum import Enum
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING
from dataclass_type_validator import dataclass_type_validator

if TYPE_CHECKING:
    from task import TaskStatus, TaskExitCode
    from generic import Output


class MsgMethods(Enum):
    REQUEST = "REQUEST"
    RESPONSE = "RESPONSE"


@dataclass
class MsgRequest:
    """
    Client Request new task to app
    """

    class alias:
        ID = "id"
        FUNCTION_NAME = "function_name"
        FUNCTION_KWARGS = "function_kwargs"

    id: str
    function_name: str
    function_kwargs: dict

    def __post_init__(self):
        dataclass_type_validator(self)

    def to_dict(self) -> dict:
        return {
            MsgRequest.alias.ID: self.id,
            MsgRequest.alias.FUNCTION_NAME: self.function_name,
            MsgRequest.alias.FUNCTION_KWARGS: self.function_kwargs,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())


@dataclass
class MsgResponse:
    """
    Response from application of completed task
    """

    class alias:
        ID = "id"
        STATUS = "status"
        OUTPUT = "output"
        EXIT_CODE = "exit_code"

    id: str
    status: "TaskStatus"
    output: "Output"
    exit_code: "TaskExitCode"

    def __post_init__(self):
        dataclass_type_validator(self)

    def to_dict(self) -> dict:
        return {
            MsgResponse.alias.ID: self.id,
            MsgResponse.alias.STATUS: self.status.value,
            MsgResponse.alias.OUTPUT: self.output.to_json_repr(),
            MsgResponse.alias.EXIT_CODE: self.exit_code.value
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict())
