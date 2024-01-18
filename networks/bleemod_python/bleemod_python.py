from networks.bleemod_python.ble_model_scanning import BLEScanner
from networks.bleemod_python.ble_model_connected import BLEConnected
from networks.bleemod_python.ble_model_discovery import BLEDiscovery
from networks.bleemod_python.ble_model_connection_establishment import BLEConnectionEstablishment
from networks.bleemod_python.ble_model_params_connection_establishment import BLEConnectionEstablishmentParams


class BLEEMod:
    """
    Implements BLE networks. Reference work done by Kindt P. et al.
    (https://webarchiv.typo3.tum.de/EI/ls-rcs/rcs/forschung/wireless-sensor-networks/bleemod/index.html)
    """
    def __init__(self):
        """
        We translated the C-library implementation to Python for code consistency.
        We opted to implement the library as a set of classes for different BLE states.
        """
        self.scanner = BLEScanner()
        self.discovery = BLEDiscovery()
        self.connected = BLEConnected()
        self.connection_establishment = BLEConnectionEstablishment()
        self.connection_establishment_params = BLEConnectionEstablishmentParams()
        self.comm_distance = 50  # meters effective communication distance for BLE
