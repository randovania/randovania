import io
import json
from typing import BinaryIO

from randovania import prime_binary_decoder


def test_simple_round_trip():
    sample_data = {
    }


def test_complex_encode(test_files_dir):
    with test_files_dir.join("prime_data_as_json.json").open("r") as data_file:
        data = json.load(data_file)
    b = io.BytesIO()
    b_io = b  # type: BinaryIO

    # Run
    prime_binary_decoder.encode(data, b_io)
