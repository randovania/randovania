from randovania.lib.signal import RdvSignal


class ExecutorToConnectorSignals:
    new_inventory = RdvSignal[[str]]()
    new_collected_locations = RdvSignal[[bytes]]()
    new_received_pickups = RdvSignal[[str]]()
    new_player_location = RdvSignal[[str]]()
    connection_lost = RdvSignal()
