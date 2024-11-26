from networks.bleemod_python.ble_model_scanning import BLEScanner
from networks.bleemod_python.ble_model_connected import BLEConnected
from networks.bleemod_python.ble_model_discovery import BLEDiscovery
from networks.bleemod_python.ble_model_connection_establishment import BLEConnectionEstablishment
from networks.bleemod_python.ble_model_params_connection_establishment import BLEConnectionEstablishmentParams

from util import get_config, load_config


class BLEEMod:
    """
    Implements BLE networks. Reference work done by Kindt P. et al.
    (https://webarchiv.typo3.tum.de/EI/ls-rcs/rcs/forschung/wireless-sensor-networks/bleemod/index.html)
    """
    def __init__(self, config=None):
        """
        We translated the C-library implementation to Python for code consistency.
        We opted to implement the library as a set of classes for different BLE states.
        """
        self.scanner = BLEScanner()
        self.discovery = BLEDiscovery()
        self.connected = BLEConnected()
        self.connection_establishment = BLEConnectionEstablishment()
        self.connection_establishment_params = BLEConnectionEstablishmentParams()

        if config is None:
            self.config = get_config()['BLE']  # load BLE config
            self.comm_distance = self.config['comm_distance']  # meters effective communication distance for BLE
            self.voltage = self.config['voltage']  # Assume 3.3 volts
        # to allow for optimization_testing.py
        else:
            # Load YAML file
            config = load_config(file_path='../config.yaml')
            self.config = config['BLE']  # load BLE config
            self.comm_distance = self.config['comm_distance']  # meters effective communication distance for BLE
            self.voltage = self.config['voltage']  # Assume 3.3 volts

