import json
from dataclasses import dataclass
from typing import Iterator, Tuple

from randovania.bitpacking import bitpacking
from randovania.bitpacking.bitpacking import BitPackValue, BitPackDecoder
from randovania.games import default_data
from randovania.games.game import RandovaniaGame
from randovania.interface_common.preset_manager import PresetManager
from randovania.layout.preset import Preset

_PERMALINK_MAX_SEED = 2 ** 31
_PERMALINK_PLAYER_COUNT_LIMITS = (2, 256)


def _game_db_hash(game: RandovaniaGame) -> int:
    data = default_data.read_json_then_binary(game)[1]
    return bitpacking.single_byte_hash(json.dumps(data, separators=(',', ':')).encode("UTF-8"))


def _get_unique_games(presets: list[Preset]) -> Iterator[RandovaniaGame]:
    games = set()
    for preset in presets:
        if preset.game not in games:
            games.add(preset.game)
            yield preset.game


@dataclass(frozen=True)
class GeneratorParameters(BitPackValue):
    seed_number: int
    spoiler: bool
    presets: list[Preset]

    def __post_init__(self):
        if self.seed_number is None:
            raise ValueError("Missing seed number")
        if not (0 <= self.seed_number < _PERMALINK_MAX_SEED):
            raise ValueError("Invalid seed number: {}".format(self.seed_number))

        if not isinstance(self.presets, list):
            raise ValueError("presets must be a list")

        object.__setattr__(self, "__cached_as_bytes", None)

    def bit_pack_encode(self, metadata) -> Iterator[Tuple[int, int]]:
        yield self.seed_number, _PERMALINK_MAX_SEED
        yield from bitpacking.encode_bool(self.spoiler)
        yield from bitpacking.encode_int_with_limits(self.player_count, _PERMALINK_PLAYER_COUNT_LIMITS)

        manager = PresetManager(None)
        for preset in self.presets:
            yield from preset.bit_pack_encode({"manager": manager})

        for game in _get_unique_games(self.presets):
            yield _game_db_hash(game), 256

    @classmethod
    def bit_pack_unpack(cls, decoder: BitPackDecoder, metadata) -> "GeneratorParameters":
        seed_number = decoder.decode_single(_PERMALINK_MAX_SEED)
        spoiler = bitpacking.decode_bool(decoder)
        player_count = bitpacking.decode_int_with_limits(decoder, _PERMALINK_PLAYER_COUNT_LIMITS)
        manager = PresetManager(None)

        presets = [
            Preset.bit_pack_unpack(decoder, {"manager": manager})
            for _ in range(player_count)
        ]
        for game in _get_unique_games(presets):
            included_data_hash = decoder.decode_single(256)
            expected_data_hash = _game_db_hash(game)
            if included_data_hash != expected_data_hash:
                raise ValueError("Given permalink is for a Randovania {} database with hash '{}', "
                                 "but current database has hash '{}'.".format(game.long_name,
                                                                              included_data_hash,
                                                                              expected_data_hash))

        return GeneratorParameters(seed_number, spoiler, presets)

    @property
    def as_bytes(self) -> bytes:
        key = "__cached_as_bytes"
        result = object.__getattribute__(self, key)
        if result is None:
            result = bitpacking.pack_value(self)
            object.__setattr__(self, key, result)

        return result

    @classmethod
    def from_bytes(cls, b: bytes) -> "GeneratorParameters":
        decoder = BitPackDecoder(b)
        result = GeneratorParameters.bit_pack_unpack(decoder, {})
        decoder.ensure_data_end()
        return result

    @property
    def player_count(self) -> int:
        return len(self.presets)

    def get_preset(self, index: int) -> Preset:
        return self.presets[index]
