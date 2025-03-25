from randovania.gui.lib.signal import RdvSignal


class ExecutorToConnectorSignals:
    new_inventory: RdvSignal[str]
    new_collected_locations: RdvSignal[bytes]
    new_received_pickups: RdvSignal[str]
    new_player_location: RdvSignal[str]
    connection_lost: RdvSignal

    def __init__(self) -> None:
        self.new_inventory = RdvSignal()
        self.new_collected_locations = RdvSignal()
        self.new_received_pickups = RdvSignal()
        self.new_player_location = RdvSignal()
        self.connection_lost = RdvSignal()
