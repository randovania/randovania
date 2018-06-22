import os

import dataset as dataset
from appdirs import AppDirs

dirs = AppDirs("Randovania", False)

_db = None


def db():
    global _db
    if _db is None:
        _db = dataset.connect('sqlite:///{}'.format(os.path.join(dirs.user_data_dir, "persistence.sqlite3")))
    return _db
