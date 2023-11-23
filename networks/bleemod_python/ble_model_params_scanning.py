# ble_model_params_scanning.py

BLE_E_MOD_SCAN_DPRE = 0.700e-3      # Duration [s] for wakeup & preprocessing for scan events
BLE_E_MOD_SCAN_DRXTX = 0.115e-3     # Duration [s] for switching from the reception of the advertising packet to the sending of the SCAN_REQ / CON_REQ packet
BLE_E_MOD_SCAN_DPRETX = 0.014e-3    # The TX phase of the scan request / connection request packet or whatever is sent is by this duration longer than 8 microseconds * bytes sent. Unit: [s].
BLE_E_MOD_SCAN_DTXRX = 0.089e-3     # Duration [s] for switching from sending the SCAN_REQ packet to receiving the SCAN_RESP packet. In the case of a CON_REQ packet, this phase does not occur.
BLE_E_MOD_SCAN_DPRERX = 0.074e-3    # The reception of the scan response is by this duration longer than 8 microseconds * bytes received. In the case of a CON_REQ packet, this phase does not occur. Unit: [s].
BLE_E_MOD_SCAN_DRXRX = 0.377e-3     # Duration [s] for switching from the reception of a SCAN_REQ packet to the continuation of the scanning. In the case of a CON_REQ packet, this phase does not occur.
BLE_E_MOD_SCAN_DPOST = 0.816e-3    # Duration [s] of the postprocessing phase of a scan event.
BLE_E_MOD_SCAN_DWOFFSET = -1.85e-3  # The scan window in the power curve usually is longer than the ideal scan window that was set by the application. Usually, this value is negative. Unit: [s]
BLE_E_MOD_SCAN_DCHCH = 1.325e-3     # Duration [s] for channel changing in continuous scanning-

BLE_E_MOD_SCAN_IPRE = 7.087e-3      # Current magnitude [A] of wakerup&preprocessing phase
BLE_E_MOD_SCAN_IRX = 26.399e-3      # Current magnitude [A] of Rx phase
BLE_E_MOD_SCAN_IRXTX = 15.011e-3    # Current magnitude [A] of Rx2Tx phase
BLE_E_MOD_SCAN_ITX = 35.999e-3      # Current magnitude [A] of Tx phase
BLE_E_MOD_SCAN_ITXRX = 16.670e-3    # Current magnitude [A] of Tx2Rx phase
BLE_E_MOD_SCAN_IRXS = 26.426e-3     # Current magnitude [A] of "Rx of scan response" phase
BLE_E_MOD_SCAN_IRXRX = 9.633e-3     # Current magnitude [A] of Rx2Rx phase
BLE_E_MOD_SCAN_IPOST = 8.012e-3    # Current magnitude [A] of postprocessing phase
BLE_E_MOD_SCAN_ICHCH = 8.550e-3    # Current magnitude [a] for channel changing in constant scanning

BLE_E_MOD_SCAN_QCTX = -0.2264e-6    # Correction offset Tx [As]
BLE_E_MOD_SCAN_QCRX = -0.1350e-6    # Correction offset Rx [As]
