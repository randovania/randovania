import datetime
import logging

import flask


def logger() -> logging.Logger:
    return flask.current_app.logger


def datetime_now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)
