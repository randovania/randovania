from __future__ import annotations

from randovania.network_common import error


def test_code():
    all_errors = list(error.BaseNetworkError.__subclasses__())

    actual_codes = {ret_cls: ret_cls.code() for ret_cls in all_errors}
    expected_codes = {ret_cls: code + 1 for code, ret_cls in enumerate(all_errors)}
    assert actual_codes == expected_codes
