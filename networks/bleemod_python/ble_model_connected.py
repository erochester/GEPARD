import numpy as np
from networks.bleemod_python.ble_model_params import *
from networks.bleemod_python.ble_model_scanning import BLEScanner


# maximum number of communication sequences possible
BLE_E_MODE_INT_MAXSEQUENCES = 15  # Adjust as needed


class BLEConnected:
    """
    BLE Energy model for the connected mode
    """
    def ble_e_model_c_get_charge_constant_parts(self):
        """
        Returns the charge of all constant parts of the model.
        These are: head, preprocessing, transient state, postprocessing, tail
        :return: charge of all constant parts [C]
        """
        return (BLE_E_MOD_C_DHEAD * BLE_E_MOD_C_IHEAD + BLE_E_MOD_C_DPRE * BLE_E_MOD_C_IPRE + BLE_E_MOD_C_DCPRE *
                BLE_E_MOD_C_ICPRE + BLE_E_MOD_C_DTRA * BLE_E_MOD_C_ITRA + BLE_E_MOD_C_DPOST * BLE_E_MOD_C_IPOST +
                BLE_E_MOD_C_DTAIL * BLE_E_MOD_C_ITAIL)

    def ble_e_model_c_get_duration_constant_parts(self):
        """
        Returns the duration of all constant parts of the model.
        These are: head, preprocessing, transient state, postprocessing, tail
        :return: duration of all constant parts [t]
        """
        return (BLE_E_MOD_C_DHEAD + BLE_E_MOD_C_DPRE + BLE_E_MOD_C_DCPRE + BLE_E_MOD_C_DTRA + BLE_E_MOD_C_DPOST +
                BLE_E_MOD_C_DTAIL)

    def ble_e_model_c_get_charge_sequences(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power):
        """
        Returns the charge of the communication sequence phases. Each sequence may have a unique number of bytes sent
        and received.
        These are: Communication preamble, Window-Widening (slave), Rx, Rx2Tx,Tx,Tx2Rx
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: charge consumed by the sequences [C]
        """
        cnt = 0
        charge = 0
        i_tx = 0

        # Determine TX current drawn determined by the Tx Power level
        if tx_power == 3:
            i_tx = BLE_E_MOD_C_ITX
        else:
            print(f"Invalid tx power level: {tx_power}")
            return 0

        # Go through all sequences
        for cnt in range(n_seq):
            # Charge consumed by RX-phase overheads (dPreRx + windowWidening)
            if cnt == 0 and not master_or_slave:
                # First rx - window widening  and longer dPreRx @ slave
                charge += (BLE_E_MOD_C_DPRERX_SL1 + (BLE_E_MOD_G_SCA * 2.0 / 1.0e6) * Tc) * BLE_E_MOD_C_IRX
            else:
                # Not the first rx phase or the first RX-phase of master - no window-widening and normal dPreRx
                charge += BLE_E_MOD_C_DPRERX * BLE_E_MOD_C_IRX

            # Charge consumed by reception
            charge += 8.0e-6 * n_rx[cnt] * BLE_E_MOD_C_IRX

            # Charge consumed by transmission + dPreTx
            charge += (BLE_E_MOD_C_DPRETX + 8.0e-6 * n_tx[cnt]) * i_tx

            # rx2tx and tx2rx interframe spaces
            charge += BLE_E_MOD_C_DRXTX * BLE_E_MOD_C_IRXTX
            charge += BLE_E_MOD_C_DTXRX * BLE_E_MOD_C_ITXRX

            # Add sequence correction offset
            charge += BLE_E_MOD_C_QTO

        # Remove leftover IFS
        if master_or_slave:
            # Master
            charge -= BLE_E_MOD_C_DRXTX * BLE_E_MOD_C_IRXTX
        else:
            # Slave
            charge -= BLE_E_MOD_C_DTXRX * BLE_E_MOD_C_ITXRX

        return charge

    def ble_e_model_c_get_charge_sequences_same_payload(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power):
        """
        Returns the charge of the communication sequence phases. Each must have the same number of bytes sent or received
        (to overcome this limitation, please use ble_e_model_c_getChargeSequences() )
        These sequences are: Communication preamble, Window-Widening (slave), Rx, Rx2Tx,Tx,Tx2Rx
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: Charge consumed by the sequences [C]
        """
        charge = 0
        n_rxa = np.full(BLE_E_MODE_INT_MAXSEQUENCES, n_rx, dtype=int)
        n_txa = np.full(BLE_E_MODE_INT_MAXSEQUENCES, n_tx, dtype=int)
        charge = self.ble_e_model_c_get_charge_sequences(master_or_slave, Tc, n_seq, n_rxa, n_txa, tx_power)
        return charge

    def ble_e_model_c_get_duration_sequences(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power):
        """
        Returns the duration of the communication sequence phases. Each sequence may have a unique number of bytes sent
        and received.
        Sequences accounted for are: Communication preamble, Window-Widening (slave), Rx, Rx2Tx,Tx,Tx2Rx
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: Time taken by the communication sequences [s]
        """
        cnt = 0
        duration = 0

        # Go through all sequences
        for cnt in range(n_seq):
            # Time consumed by RX-phase overheads (dPreRx + windowWidening)
            if cnt == 0 and not master_or_slave:
                # First rx - window widening  and longer dPreRx @ slave
                duration += BLE_E_MOD_C_DPRERX_SL1 + BLE_E_MOD_G_SCA * 2.0 / 1.0e6 * Tc
            else:
                # Not the first rx phase or the first RX-phase of master - no window-widening and normal dPreRx
                duration += BLE_E_MOD_C_DPRERX

            # Time consumed by reception
            duration += 8.0e-6 * n_rx[cnt]

            # Time consumed by transmission + dPreTx
            duration += BLE_E_MOD_C_DPRETX + 8.0e-6 * n_tx[cnt]

            # rx2tx and tx2rx interframe spaces
            duration += BLE_E_MOD_C_DRXTX
            duration += BLE_E_MOD_C_DTXRX

        # Remove leftover IFS
        if master_or_slave:
            # Master
            duration -= BLE_E_MOD_C_DRXTX
        else:
            # Slave
            duration -= BLE_E_MOD_C_DTXRX

        return duration

    def ble_e_model_c_get_duration_sequences_same_payload(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power):
        """
        Returns the time spent by the communication sequence phases. Each must have the same number of bytes sent
        or received (to overcome this limitation, please use ble_e_model_c_getDurationSequences() )
        These sequences are: Communication preamble, Window-Widening (slave), Rx, Rx2Tx,Tx,Tx2Rx
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: Time spent within the communication sequences [s]
        """
        duration = 0
        n_rxa = np.full(BLE_E_MODE_INT_MAXSEQUENCES, n_rx, dtype=int)
        n_txa = np.full(BLE_E_MODE_INT_MAXSEQUENCES, n_tx, dtype=int)
        duration = self.ble_e_model_c_get_duration_sequences(master_or_slave, Tc, n_seq, n_rxa, n_txa, tx_power)
        return duration

    def ble_e_model_c_get_charge_event(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power):
        """
        Returns the charge consume dby a BLE connection event. Each sequence may have a unique number of bytes sent
        and received.
        The sleep duration in the connection interval is not accounted for.
        See ble_e_model_c_getChargeConnectionInterval() for the charge consumed per interval.
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: Charge consumed by the connection event [C]
        """
        charge = self.ble_e_model_c_get_charge_constant_parts()
        charge += self.ble_e_model_c_get_charge_sequences(master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power)
        return charge

    def ble_e_model_c_get_charge_event_same_payload(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power):
        """
        Returns the charge consumed by a BLE connection event.
        Each sequence must have the same number of bytes sent and received.
        The sleep duration in the connection interval is not accounted for.
        See ble_e_model_c_getChargeConnectionInterval() for the charge consumed per interval.
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: Charge consumed by the connection event [C]
        """
        charge = self.ble_e_model_c_get_charge_constant_parts()
        charge += self.ble_e_model_c_get_charge_sequences_same_payload(master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power)
        return charge

    def ble_e_model_c_get_duration_event(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power):
        """
        Returns the duration of a BLE connection event. Each sequence may have a unique number of bytes sent and received.
        The sleep duration in the connection interval is not accounted for.
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: Duration of the connection event [s]
        """
        duration = self.ble_e_model_c_get_duration_constant_parts()
        duration += self.ble_e_model_c_get_duration_sequences(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power)
        return duration

    def ble_e_model_c_get_duration_event_same_payload(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power):
        """
        Returns the duration of a BLE connection event. Each sequence must have the same number of bytes sent and received.
        The sleep duration in the connection interval is not accounted for.
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: Duration of the connection event [s]
        """
        duration = self.ble_e_model_c_get_duration_constant_parts()
        duration += self.ble_e_model_c_get_duration_sequences_same_payload(master_or_slave, Tc, n_seq, n_rx, n_tx,
                                                                           tx_power)
        return duration

    def ble_e_model_c_get_charge_connection_interval(self, master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power):
        """
        Returns the charge consumed within a BLE connection interval.
        It includes both the connection event and the sleep duration.
        Each sequence may have a unique number of bytes sent and received.
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: Charge consumed within one connection interval [C]
        """
        duration = self.ble_e_model_c_get_duration_event(master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power)
        charge = self.ble_e_model_c_get_charge_event(master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power)
        charge += (Tc - duration) * BLE_E_MOD_G_ISL
        return charge

    def ble_e_model_c_get_charge_connection_interval_same_payload(self, master_or_slave, Tc, n_seq, n_rx, n_tx,
                                                                  tx_power):
        """
        Returns the charge consumed within a BLE connection interval.
        It includes both the connection event and the sleep duration.
        Each sequence may have a unique number of bytes sent and received.
        :param master_or_slave: 1=>master, 0=>Slave. For the slave, Rx and Tx are swapped (Master: first Tx, then Rx;
        Slave: first Rx, then Tx) and there is window-widening and a longer dPreRx for the first sequence in an event.
        :param Tc: Connection interval
        :param n_seq: Number of sequences (pairs of packets per connection event)
        :param n_rx: Number of bytes received. Each array element contains the number of bytes received per sequence
        (pair of packet). Must include all protocol overheads.
        :param n_tx: Number of bytes sent. Each array element contains the number of bytes sent per sequence
        (pair of packet). Must include all protocol overheads.
        :param tx_power: Tx-Power setting of the device
        :return: Charge consumed within one connection interval [C]
        """
        duration = self.ble_e_model_c_get_duration_event_same_payload(master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power)
        charge = self.ble_e_model_c_get_charge_event_same_payload(master_or_slave, Tc, n_seq, n_rx, n_tx, tx_power)
        charge += (Tc - duration) * BLE_E_MOD_G_ISL
        return charge
