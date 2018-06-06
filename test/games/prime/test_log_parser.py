import io

import py
import pytest

import randovania.resolver.game_description
from randovania.games.prime import log_parser


def test_parse_log(test_files_dir):
    log = log_parser.parse_log(str(test_files_dir.join("echoes_log_a.txt")))
    assert log.version == "3.2"
    assert log.seed == 1145919247
    assert log.excluded_pickups == [23]
    assert log.pickup_mapping == [88, 24, 71, 35, 103, 85, 114, 73, 54, 25, 62, 70, 10, 33, 118, 86, 1, 5, 4, 36, 8, 89,
                                  87, 23, 74, 22, 43, 116, 75, 37, 40, 15, 108, 91, 14, 72, 61, 68, 28, 64, 90, 99, 12,
                                  96, 45, 0, 66, 50, 94, 41, 77, 9, 6, 18, 83, 58, 46, 102, 2, 67, 76, 65, 42, 78, 53,
                                  105, 60, 7, 111, 106, 21, 26, 63, 19, 84, 110, 11, 112, 115, 107, 80, 47, 38, 79, 32,
                                  59, 104, 113, 51, 52, 109, 44, 56, 101, 92, 69, 30, 98, 27, 97, 49, 3, 48, 55, 31, 13,
                                  39, 95, 81, 20, 93, 29, 57, 100, 82, 117, 34, 16, 17]


@pytest.mark.parametrize("log_name", [
    "echoes_log_a.txt",
    "echoes_log_recursion_heavy.txt",
])
def test_generator(test_files_dir, log_name):
    log = log_parser.parse_log(str(test_files_dir.join(log_name)))
    generated_log = log_parser.generate_log(log.seed, log.excluded_pickups, False)
    assert log == generated_log


@pytest.mark.parametrize("log_name", [
    "echoes_log_a.txt",
    "echoes_log_recursion_heavy.txt",
])
def test_write(test_files_dir: py.path.local, log_name):
    input_file = test_files_dir.join(log_name)
    log = log_parser.parse_log(str(input_file))
    output = io.StringIO()
    log.write(output)

    assert output.getvalue().split() == input_file.read_text("utf-8").split()
