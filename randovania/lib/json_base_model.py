import typing

from pydantic import BaseModel, ConfigDict


class JsonBaseModel(BaseModel):
    """
    Base class for pydantic models that should expose the same as_json/from_json
    interface as JsonDataclass, so both can be used interchangeably in the codebase.
    """

    model_config = ConfigDict(
        from_attributes=True,
        ser_json_bytes="base64",
        val_json_bytes="base64",
    )

    @property
    def as_json(self) -> dict[str, typing.Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_json(cls, param: typing.Any, **extra: typing.Any) -> typing.Self:
        return cls.model_validate(param)
