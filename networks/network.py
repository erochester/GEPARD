from networks.bleemod_python.bleemod_python import BLEEMod
from networks.wifi import WiFi


class Network:
    def __init__(self, network_type, logger):
        self.logger = logger
        self.network_type = network_type
        # TODO: for now there is no LoRa
        if self.network_type == "ble":
            self.network_impl = BLEEMod()
        elif self.network_type == "wifi":
            self.network_impl = WiFi()

