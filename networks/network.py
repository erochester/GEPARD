from networks.bleemod_python.bleemod_python import BLEEMod
from networks.zigbee import ZigBee
from networks.lora import LoRa
import sys


class Network:
    """
    Metaclass for Network Technologies. Used to unify and call different network technology implementations.
    """
    def __init__(self, network_type, logger):
        self.logger = logger
        self.network_type = network_type
        if self.network_type == "ble":
            self.network_impl = BLEEMod()
        elif self.network_type == "zigbee":
            self.network_impl = ZigBee()
        elif self.network_type == "lora":
            self.network_impl = LoRa()
        else:
            print("Network type not supported")
            sys.exit(1)

