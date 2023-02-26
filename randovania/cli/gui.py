try:
    import PySide6  # noqa: F401

    has_gui = True
except ModuleNotFoundError:
    has_gui = False


def create_subparsers(sub_parsers):
    if has_gui:
        from randovania.gui import qt
        return qt.create_subparsers(sub_parsers)
