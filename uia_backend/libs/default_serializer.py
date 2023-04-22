from typing import Any


class StructureSerializer:
    @staticmethod
    def to_representation(data: dict[str, Any] | str | list[Any]) -> dict[str, Any]:
        return {"info": "Success", "message": data}
