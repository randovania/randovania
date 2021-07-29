from construct import PrefixedArray, VarInt, Struct

BinaryInventory = PrefixedArray(
    VarInt,
    Struct(
        index=VarInt,
        amount=VarInt,
        capacity=VarInt,
    )
)
