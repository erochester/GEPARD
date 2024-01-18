# ble_model_params_connection_establishment.py

BLE_E_MOD_CE_DTWO_CU = 0  # Transmit window offset for connection update procedures


class BLEConnectionEstablishmentParams:
    """
    Specifies/implements methods for BLE connection establishment parameters.
    """
    def BLE_E_MOD_CE_DTWO_CR(self, TcNew):
        """
        Contains a nonlinear formula depending on the future connection interval TcNew.
        :param TcNew: connection interval (s)
        :return: Transmit window offset for connection request procedures.
        """
        return TcNew - 0.006454 if TcNew > 0.0125 else 0.389 * TcNew + 0.000484

    def BLE_E_MOD_CE_DTW(self, TcNew):
        """
        Might depend on the future connection interval TcNew; for BLE112 devices it does not.
        :param TcNew: connection interval (s)
        :return: Transmit window.
        """
        return 0.003

    def BLE_E_MOD_CE_DP(self, TcNew):
        """
        :param TcNew: connection interval (s)
        :return: The average time the transmission begins after the beginning of the transmit window.
        """
        return self.BLE_E_MOD_CE_DTW(TcNew) / 2.0


# Some packet lengths occurring in connection establishment / update sequences.
BLE_E_MOD_CE_ADV_IND_PKG_LEN = 37  # Number of bytes sent in an ADV_IND advertising packet by the advertiser
BLE_E_MOD_CE_CON_REQ_LEN = 44  # Number of bytes sent in a CONNECT_REQ packet by the initiator (former scanner)
BLE_E_MOD_CE_CON_UP_LEN = 22  # Number of bytes sent in an LL_CONNECTION_UPDATE_REQ packet by the master
BLE_E_MOD_CE_CON_UP_SLRSP_LEN = 10  # Number of bytes sent by the slave to the master in the event
# an LL_CONNECTION_UPDATE_REQ packet has been received
BLE_E_MOD_CE_CON_UP_TXPOWER = 3  # Tx power level for connection update
