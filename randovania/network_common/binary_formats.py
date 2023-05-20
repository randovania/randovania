import construct
from construct import PrefixedArray, VarInt, Struct, CString

from randovania.bitpacking import construct_dataclass
from randovania.lib.construct_lib import OptionalValue
from randovania.network_client.game_session import PlayerSessionEntry, GameDetails

BinStr = CString("utf-8")

BinaryInventory = Struct(
    version=construct.Const(1, VarInt),
    game=BinStr,
    elements=PrefixedArray(
        VarInt,
        Struct(
            name=BinStr,
            amount=VarInt,
            capacity=VarInt,
        )
    )
)

BinaryPlayerSessionEntry = construct_dataclass.construct_for_type(PlayerSessionEntry)

BinaryGameDetails = construct_dataclass.construct_for_type(GameDetails)

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
