import random

from randovania.games.prime2.generator.base_patches_factory import EchoesBasePatchesFactory


def test_elevator_echoes_shuffled(echoes_game_patches, default_echoes_configuration):
    factory = EchoesBasePatchesFactory()
    rng = random.Random(1000)

    # Run
    result = factory.elevator_echoes_shuffled(default_echoes_configuration, echoes_game_patches, rng)

    # Assert
    simpler = {
        source.area_identifier.as_string: target.as_string
        for source, target in result.items()
    }
    assert simpler == {
        'Agon Wastes/Transport to Sanctuary Fortress': 'Temple Grounds/Temple Transport B',
        'Agon Wastes/Transport to Temple Grounds': 'Temple Grounds/Temple Transport A',
        'Agon Wastes/Transport to Torvus Bog': 'Temple Grounds/Temple Transport C',
        'Great Temple/Temple Transport A': 'Temple Grounds/Transport to Agon Wastes',
        'Great Temple/Temple Transport B': 'Sanctuary Fortress/Transport to Agon Wastes',
        'Great Temple/Temple Transport C': 'Torvus Bog/Transport to Agon Wastes',
        'Sanctuary Fortress/Transport to Agon Wastes': 'Great Temple/Temple Transport B',
        'Sanctuary Fortress/Transport to Temple Grounds': 'Temple Grounds/Transport to Sanctuary Fortress',
        'Sanctuary Fortress/Transport to Torvus Bog': 'Torvus Bog/Transport to Sanctuary Fortress',
        'Temple Grounds/Temple Transport A': 'Agon Wastes/Transport to Temple Grounds',
        'Temple Grounds/Temple Transport B': 'Agon Wastes/Transport to Sanctuary Fortress',
        'Temple Grounds/Temple Transport C': 'Agon Wastes/Transport to Torvus Bog',
        'Temple Grounds/Transport to Agon Wastes': 'Great Temple/Temple Transport A',
        'Temple Grounds/Transport to Sanctuary Fortress': 'Sanctuary Fortress/Transport to Temple Grounds',
        'Temple Grounds/Transport to Torvus Bog': 'Torvus Bog/Transport to Temple Grounds',
        'Torvus Bog/Transport to Agon Wastes': 'Great Temple/Temple Transport C',
        'Torvus Bog/Transport to Sanctuary Fortress': 'Sanctuary Fortress/Transport to Torvus Bog',
        'Torvus Bog/Transport to Temple Grounds': 'Temple Grounds/Transport to Torvus Bog',
    }
