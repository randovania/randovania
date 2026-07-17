import construct
import pydantic

from randovania.lib import construct_lib

BinaryPydanticModel = construct.Struct(
    magic=construct.Const(b"RDVM"),
    version=construct.Rebuild(construct.VarInt, 3),
    data=construct.Switch(
        construct.this.version,
        {
            3: construct_lib.CompressedZstdJsonValue,
        },
        construct.Error,
    ),
)


def encode_model(entry: pydantic.BaseModel) -> bytes:
    """Encodes the given pydantic model instance as a compressed JSON string."""
    as_json = entry.model_dump_json(exclude_unset=True, exclude_defaults=True)
    return BinaryPydanticModel.build(
        {
            "data": as_json,
        }
    )


def decode_model[T: pydantic.BaseModel](data: bytes, model: type[T]) -> T:
    """Decodes the given bytes created by `encode_model` into the given model."""
    return model.model_validate_json(BinaryPydanticModel.parse(data)["data"])
