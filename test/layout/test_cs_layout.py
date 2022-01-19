from randovania.games.cave_story.layout.cs_configuration import CSObjective
from randovania.games.cave_story.layout.cs_cosmetic_patches import CSCosmeticPatches, MyChar, MusicRandoType
from randovania.games.cave_story.layout.preset_describer import get_ingame_hash, get_ingame_hash_str

from randovania.games.game import RandovaniaGame


def test_cs_objective():
    for obj in CSObjective:
        try:
            assert isinstance(obj.name, str)
            assert isinstance(obj.script, str)
            assert isinstance(obj.enters_hell, bool)
        except ValueError:
            pass


def test_cs_cosmetic_patches():
    patches = CSCosmeticPatches.default()
    assert patches.game() == RandovaniaGame.CAVE_STORY

    assert {mychar for mychar in MyChar if mychar.description is not None} == {MyChar.CUSTOM, MyChar.RANDOM}

    for music in MusicRandoType:
        assert isinstance(music.description, str)


def test_cs_preset_describer():
    hash_bytes = b'\x00\x00\x00\x00\x00'
    assert get_ingame_hash(hash_bytes) == [1, 1, 1, 1, 1]
    assert get_ingame_hash_str(hash_bytes) != ""
