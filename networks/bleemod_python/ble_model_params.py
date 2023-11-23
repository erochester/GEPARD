"""
ble_model_params.py
Master include for all numerical values.
The only purpose of this file is including further modules that provide all numerical data
values for the model parameters.

(c) 2013, Philipp Kindt
(c) 2013, Lehrstuhl für Realzeit-Computersysteme (RCS), Technische Universität München (TUM)

This file is part of bleemod.

bleemod is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

bleemod is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with bleemod. If not, see <http://www.gnu.org/licenses/>
"""

from networks.bleemod_python.ble_model_params_general import *  # General parameters that do not correspond to a certain mode
from networks.bleemod_python.ble_model_params_connected import *  # Parameters for connection and advertising events
from networks.bleemod_python.ble_model_params_scanning import *  # Parameters for scan events
from networks.bleemod_python.ble_model_params_connection_establishment import *  # Parameters for establishing and updating a connection
