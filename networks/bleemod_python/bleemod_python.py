from networks.bleemod_python.ble_model_scanning import BLEScanner
from networks.bleemod_python.ble_model_connected import BLEConnected
from networks.bleemod_python.ble_model_discovery import BLEDiscovery
from networks.bleemod_python.ble_model_connection_establishment import BLEConnectionEstablishment
from networks.bleemod_python.ble_model_params_connection_establishment import BLEConnectionEstablishmentParams

class BLEEMod:
    def __init__(self):
        self.scanner = BLEScanner()
        self.discovery = BLEDiscovery()
        self.connected = BLEConnected()
        self.connection_establishment = BLEConnectionEstablishment()
        self.connection_establishment_params = BLEConnectionEstablishmentParams()
