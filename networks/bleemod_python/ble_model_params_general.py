"""
ble_model_params_general.py
Device-dependent model params for Bluegiga BLE112 devices that are independent of the mode
(connected/advertising/scanning/...)

This file contains device-dependent values for Bluegiga BLE112 devices that are independent of the mode.

Change the values for different devices. For the model, please refer to the publication
"A precise energy model for the Bluetooth Low Energy Protocol" by Philipp Kindt
"""

BLE_E_MOD_G_SCA = 50          # sleep clock accuracy (ppm)
BLE_E_MOD_G_ISL = 0.9e-6      # sleep current [A]
