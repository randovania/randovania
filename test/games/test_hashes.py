import re

from randovania.layout.layout_description import _all_hash_words


def test_hash_words() -> None:
    # Our hash cannot start or end with hyphens
    # The hash words themselves can only contain letters, digits, '-' or '.'.
    regex = re.compile(r"^(?!-)[a-zA-Z0-9-.]+(?<!-)$")

    hashes = _all_hash_words()

    for game_hash in hashes:
        print(game_hash)
        res = re.search(regex, game_hash)
        assert res is not None
