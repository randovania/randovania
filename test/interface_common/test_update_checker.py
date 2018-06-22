from unittest.mock import MagicMock, patch

from randovania.interface_common import update_checker


@patch("randovania.interface_common.update_checker._read_from_db", autospec=True)
def test_get_latest_version_work(mock_read_from_db: MagicMock):
    on_result = MagicMock()

    update_checker._get_latest_version_work(on_result)

    on_result.assert_called_once_with(
        mock_read_from_db.return_value.tag_name,
        mock_read_from_db.return_value.html_url
    )
