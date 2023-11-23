from networks.bleemod_python.ble_model_scanning import BLEScanner, BLEModelSCEventType
from networks.bleemod_python.ble_model_connected import BLEConnected
from networks.bleemod_python.ble_model_params_connection_establishment import BLEConnectionEstablishmentParams
from networks.bleemod_python.ble_model_params import *

'''
Energy model for BLE connection request procedures and for connection update procedures
This file implements a model for connection parameter update procedures and for connection request procedures
'''


class BLEConnectionEstablishment:

    def ble_e_model_ce_get_charge_for_connection_procedure(self, establishment_or_update, scan_type, master_or_slave,
                                                           Tc_old, Tc_new):
        """
        Computes the charge consumed by establishing a connection or updating the connection parameters of an
        existing connection.

        This function computes the charge consumed by a connection request procedure or connection parameter update
        procedure.
        A connection request procedure occurs, after a scanner has received an ADV_IND advertising packet
        from an advertiser. After that, the scanner might respond with an CON_REQ packet, which is the first part of the
        connection establishment procedure.
        The packet lengths of packets involved in these procedures are taken
        from the values in ble_model_params_connection_establishment.py

        The process of advertising and scanning until there is the first reception is not accounted for in this function.
        This process is referred to as neighbor discovery and needs to be modeled separately.

        :param establishment_or_update: 1 => connection establishment procedure, 0 => connection parameter update
        :param scan_type: Determines the connection comes about by continuous or periodic scanning.
        Only relevant for connection requests for initiators.
        :param master_or_slave: 1 => master, 0 => slave
        :param Tc_old:	Connection interval [s] before the parameter update. For connection establishment procedures,
        this value is ignored.
        :param Tc_new:	The future connection interval [s] after the connection request or establishment procedure
        :return: Charge consumed by the parameter update
        """
        charge = 0
        duration_event = 0
        ble_scan = BLEScanner()
        ble_connected = BLEConnected()
        ble_conn_est_params = BLEConnectionEstablishmentParams()

        if master_or_slave:
            # Master
            if establishment_or_update:
                # Connection establishment procedure
                charge = ble_scan.ble_e_model_sc_get_charge_scan_event(0,
                                                                       BLEModelSCEventType.SC_EVENT_TYPE_CON_REQ_OFFSET,
                                                                       scan_type,
                                                                       BLE_E_MOD_CE_ADV_IND_PKG_LEN,
                                                                       BLE_E_MOD_CE_CON_REQ_LEN, 0, 0)
                charge += (0.00125 + ble_conn_est_params.BLE_E_MOD_CE_DTWO_CR(Tc_new) + ble_conn_est_params.BLE_E_MOD_CE_DP(Tc_new)) * BLE_E_MOD_G_ISL
            else:
                # Connection update procedure
                charge = ble_connected.ble_e_model_c_get_charge_event_same_payload(1, 0, 1,
                                                                                   BLE_E_MOD_CE_CON_UP_SLRSP_LEN,
                                                                                   BLE_E_MOD_CE_CON_UP_LEN,
                                                                                   BLE_E_MOD_CE_CON_UP_TXPOWER)
                duration_event = ble_connected.ble_e_model_c_get_duration_event_same_payload(1, 0, 1,
                                                                                             BLE_E_MOD_CE_CON_UP_SLRSP_LEN,
                                                                                             BLE_E_MOD_CE_CON_UP_LEN,
                                                                                             BLE_E_MOD_CE_CON_UP_TXPOWER)
                charge += (Tc_old + 0.0 + ble_conn_est_params.BLE_E_MOD_CE_DP(Tc_new) - duration_event) * BLE_E_MOD_G_ISL

        else:
            # Slave
            if establishment_or_update:
                # Connection establishment procedure
                charge = (0.00125 + ble_conn_est_params.BLE_E_MOD_CE_DTWO_CR(Tc_new) - (BLE_E_MOD_G_SCA * 2.0 / 1e6) *
                          (0.00125 + ble_conn_est_params.BLE_E_MOD_CE_DTWO_CR(Tc_new))) * BLE_E_MOD_G_ISL + \
                         (ble_conn_est_params.BLE_E_MOD_CE_DP(Tc_new) + (BLE_E_MOD_G_SCA * 2.0 / 1e6) *
                          (0.00125 + ble_conn_est_params.BLE_E_MOD_CE_DTWO_CR(Tc_new))) * BLE_E_MOD_SCAN_IRX
            else:
                # Connection update procedure
                charge = ble_connected.ble_e_model_c_get_charge_event_same_payload(0, Tc_old, 1,
                                                                                   BLE_E_MOD_CE_CON_UP_LEN,
                                                                                   BLE_E_MOD_CE_CON_UP_SLRSP_LEN,
                                                                                   BLE_E_MOD_CE_CON_UP_TXPOWER)
                duration_event = ble_connected.ble_e_model_c_get_duration_event_same_payload(0, Tc_old, 1,
                                                                                             BLE_E_MOD_CE_CON_UP_LEN,
                                                                                             BLE_E_MOD_CE_CON_UP_SLRSP_LEN,
                                                                                             BLE_E_MOD_CE_CON_UP_TXPOWER)
                charge += (Tc_old + 0.0 - (BLE_E_MOD_G_SCA * 2.0 / 1e6) * Tc_old - duration_event) * BLE_E_MOD_G_ISL
                charge += (ble_conn_est_params.BLE_E_MOD_CE_DP(Tc_new) + (BLE_E_MOD_G_SCA * 2.0 / 1e6) * Tc_old) * BLE_E_MOD_SCAN_IRX

        return charge
