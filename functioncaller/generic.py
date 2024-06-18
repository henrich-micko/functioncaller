from typing import Any


class Output:
    def __init__(self, value: Any = None) -> None:
        self.value = value
        Output.validate(self.value)

    @staticmethod
    def validate(value) -> None:
        from json import dumps
        dumps(value)

    def to_json_repr(self) -> Any:
        return self.value
