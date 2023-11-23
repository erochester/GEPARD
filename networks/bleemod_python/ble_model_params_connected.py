# ble_model_params_connected.py

BLE_E_MOD_C_DHEAD = 0.578e-3      # Duration of head phase [s]
BLE_E_MOD_C_DPRE = 0.305e-3       # Duration of preprocessing phase [s]
BLE_E_MOD_C_DCPRE = 0.073e-3      # Duration of communication preamble phase [s]
BLE_E_MOD_C_DPRERX = 0.123e-3     # Duration of the prerx phase [s] for the master and for the slave except the first rx-phase of the slave within an event. The first duration of a slave is longer, see BLE_E_MOD_C_DPRERX_SL1. The prerx phase is the phase where the receiver is switched on, but no bits are transmitted. Therefore, the rx-phase is by dprerx longer than 8 microseconds * bytes received
BLE_E_MOD_C_DPRERX_SL1 = 0.388e-3  # Duration of the first prerx phase [s] of a slave. It is longer than different prerx phases and not related to window-widening. See BLE_E_MOD_C_DPRERX_SL
BLE_E_MOD_C_DRXTX = 0.08e-3       # Duration of the Rx2Tx-phase [s]
BLE_E_MOD_C_DPRETX = 0.053e-3     # Duration of the pretx phase [s] (tx-phase is longer than 8 microseconds * bytes sent as the radio has to prepare)
BLE_E_MOD_C_DTXRX = 0.057e-3      # Duration of the Rx2Rx-phase [s]
BLE_E_MOD_C_DTRA = 0.066e-3       # Duration of the transient phase [s]
BLE_E_MOD_C_DPOST = 0.860e-3      # Duration of the postprocessing phase [s]
BLE_E_MOD_C_DTAIL = 0.08e-3       # Duration of the tail phase [s]
BLE_E_MOD_C_IHEAD = 5.924e-3      # Current magnitude of the head phase [A]
BLE_E_MOD_C_IPRE = 7.691e-3       # Current magnitude of the preprocessing phase [A]
BLE_E_MOD_C_ICPRE = 12.238e-3     # Current magnitude of the communication preamble phase [A]
BLE_E_MOD_C_IRX = 26.505e-3       # Current magnitude of the reception phase [A]
BLE_E_MOD_C_IRXTX = 14.128e-3     # Current magnitude of the Rx2Tx phase [A]
BLE_E_MOD_C_ITX = 36.445e-3       # Current magnitude of the Tx phase [A]
BLE_E_MOD_C_ITXRX = 15.125e-3     # Current magnitude of the Tx2Rx phase [A]
BLE_E_MOD_C_ITRA = 11.636e-3      # Current magnitude of the transient phase [A]
BLE_E_MOD_C_IPOST = 7.980e-3      # Current magnitude of the postprocessing phase [A]
BLE_E_MOD_C_ITAIL = 4.129e-3      # Current magnitude of the tail phase [A]
BLE_E_MOD_C_QTO = -1.2e-6         # Communication sequence correction offset [As]
