"""
ble_model_params.py
Master include for all numerical values.
The only purpose of this file is including further modules that provide all numerical data
values for the model parameters.
"""

from networks.bleemod_python.ble_model_params_general import *  # General parameters that do not correspond
# to a certain mode
from networks.bleemod_python.ble_model_params_connected import *  # Parameters for connection and advertising events
from networks.bleemod_python.ble_model_params_scanning import *  # Parameters for scan events
from networks.bleemod_python.ble_model_params_connection_establishment import *  # Parameters for
# establishing and updating a connection
