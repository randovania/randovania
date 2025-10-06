from __future__ import annotations

import copy

import pytest

from randovania.lib import obfuscator


def test_round_trip_json(obfuscator_test_secret: None) -> None:
    original = {"foo": 1234, "bar": ["a", "b", 5]}
    encrypted = obfuscator.obfuscate_json(copy.deepcopy(original))
    result = obfuscator.deobfuscate_json(encrypted)

    assert result == original


def test_round_trip_raw(obfuscator_test_secret: None) -> None:
    original = b"abcfefaw512312t"
    encrypted = obfuscator.obfuscate(original)
    result = obfuscator.deobfuscate(encrypted)

    assert result == original


def test_decode_raw(obfuscator_test_secret: None) -> None:
    encrypted = "gAAAAABo44Ew2ZrUo7HzDQ3RowFJ8Npto8SetNJ2tBELbFkzl8UOnPw8yskWXHBXtbuLniLk8ZTzmomhavVCACj0MeNvHoNSLg=="
    result = obfuscator.deobfuscate(encrypted)

    assert result == b"abcfefaw512312t"


def test_obfuscate_no_secret(obfuscator_no_secret: None) -> None:
    with pytest.raises(obfuscator.MissingSecret):
        obfuscator.obfuscate_json({"foo": 1234, "bar": ["a", "b", 5]})


def test_obfuscate_env_secret(obfuscator_no_secret: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OBFUSCATOR_SECRET", "cNGtDlTqCYF3BFCAQTaDSo5O7DQtzjsd3mS801MPM_M=")

    encrypted = "gAAAAABo44Ew2ZrUo7HzDQ3RowFJ8Npto8SetNJ2tBELbFkzl8UOnPw8yskWXHBXtbuLniLk8ZTzmomhavVCACj0MeNvHoNSLg=="
    result = obfuscator.deobfuscate(encrypted)

    assert result == b"abcfefaw512312t"
