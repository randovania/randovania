from construct import PrefixedArray, VarInt, Struct, CString, Flag

from randovania.lib.construct_lib import OptionalValue

BinStr = CString("utf-8")

OldBinaryInventory = PrefixedArray(
    VarInt,
    Struct(
        index=VarInt,
        amount=VarInt,
        capacity=VarInt,
    )
)

BinaryInventory = PrefixedArray(
    VarInt,
    Struct(
        name=BinStr,
        amount=VarInt,
        capacity=VarInt,
    )
)

BinaryPlayerSessionEntry = Struct(
    id=VarInt,
    name=BinStr,
    row=OptionalValue(VarInt),
    admin=Flag,
    connection_state=BinStr,
)

BinaryGameDetails = Struct(
    seed_hash=BinStr,
    word_hash=BinStr,
    spoiler=Flag,
)

BinaryGameSessionEntry = Struct(
    id=VarInt,
    name=BinStr,
    presets=PrefixedArray(VarInt, BinStr),
    players=PrefixedArray(VarInt, BinaryPlayerSessionEntry),
    game_details=OptionalValue(BinaryGameDetails),
    state=BinStr,
    generation_in_progress=OptionalValue(VarInt),
    allowed_games=PrefixedArray(VarInt, BinStr),
)

BinaryGameSessionAction = Struct(
    location=VarInt,
    pickup=BinStr,
    provider=BinStr,
    provider_row=VarInt,
    receiver=BinStr,
    time=BinStr,
)
BinaryGameSessionActions = PrefixedArray(VarInt, BinaryGameSessionAction)

BinaryGameSessionAudit = Struct(
    user=BinStr,
    message=BinStr,
    time=BinStr,
)
BinaryGameSessionAuditLog = PrefixedArray(VarInt, BinaryGameSessionAudit)
