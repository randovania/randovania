import py
import pytest

from randovania.games.prime import binary_data, log_parser
from randovania.resolver.data_reader import read_resource_database
from randovania.resolver.echoes import ResolverConfiguration, run_resolver


@pytest.mark.parametrize(["log_name", "is_valid"], [
    ("prime2_original_log.txt", True),
    ("echoes_log_a.txt", False),
    ("echoes_log_recursion_heavy.txt", False),
])
def test_log_files(test_files_dir: py.path.local, log_name: str, is_valid: bool):
    data = binary_data.decode_default_prime2()
    randomizer_log = log_parser.parse_log(str(test_files_dir.join(log_name)))

    enabled_tricks = {
        trick.index
        for trick in read_resource_database(data["resource_database"]).trick
    }

    resolver_config = ResolverConfiguration(5, 0, enabled_tricks, True)

    final_state = run_resolver(data, randomizer_log, resolver_config)
    if is_valid:
        assert final_state
    else:
        assert final_state is None
