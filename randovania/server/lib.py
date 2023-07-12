import logging

import flask


def logger() -> logging.Logger:
    return flask.current_app.logger
