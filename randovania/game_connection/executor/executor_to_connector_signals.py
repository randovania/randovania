from PySide6.QtCore import QObject, Signal


class ExecutorToConnectorSignals(QObject):
    new_inventory = Signal(str)
    new_collected_locations = Signal(bytes)
    new_received_pickups = Signal(str)
    new_player_location = Signal(str)
    connection_lost = Signal()
