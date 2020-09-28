try:
    import PySide2

    has_gui = True
except ModuleNotFoundError as e:
    has_gui = False


def create_subparsers(sub_parsers):
    if has_gui:
        from randovania.gui import qt
        return qt.create_subparsers(sub_parsers)
