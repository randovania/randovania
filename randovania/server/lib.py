from __future__ import annotations

from typing import TYPE_CHECKING

import flask

if TYPE_CHECKING:
    import logging


def logger() -> logging.Logger:
    return flask.current_app.logger
