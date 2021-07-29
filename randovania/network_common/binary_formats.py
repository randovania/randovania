from construct import PrefixedArray, VarInt, Struct, CString, Flag

from randovania.games.binary_data import OptionalValue

BinStr = CString("utf-8")

BinaryInventory = PrefixedArray(
    VarInt,
    Struct(
        index=VarInt,
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
    permalink=BinStr,
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
