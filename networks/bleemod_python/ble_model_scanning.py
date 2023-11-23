# ble_model_scanning.py
from networks.bleemod_python.ble_model_params import *
from enum import Enum

'''
Energy model for BLE scan events
'''


class BLEModelSCEventType(Enum):
    """
    The type of scan event
    """
    SC_EVENT_TYPE_NO_RECEPTION = 0  # Scan event that does not receive anything
    SC_EVENT_TYPE_PASSIVE_SCANNING = 1  # Scan event for passive scanning.
    # No matter if advertising packets are received or not, this type is valid for passive scanning.
    # Only exception: A CON_REQ packet is sent
    SC_EVENT_TYPE_ACTIVE_SCANNING = 2  # Scan event for active scanning without connecting.
    # An advertising packet is received within this event, otherwise,
    # it would be idle scanning and \ref SC_EVENT_TYPE_NO_RECEPTION must be used.
    SC_EVENT_TYPE_CON_REQ = 3  # Connection request packet is sent within that scan event.
    # Takes into account whole scan event.
    SC_EVENT_TYPE_CON_REQ_OFFSET = 4  # Connection request packet is sent within that scan event.
    # This type only takes into account the energy spent for the additional energy compared to an idle scan event
    # without reception which is aborted after the reception of an ADV_IND packet.
    # This energy consists of the CON_REQ packet and drxtx, only! It is used for compatibility
    # with the discovery energy model: To get the energy for discovery + connection,
    # add the discovery energy and a packet of this type!
    SC_EVENT_TYPE_ABORTED = 5


class BLEModelSCScanType(Enum):
    """
    Determines whether we use continuous or periodic scanning
    """
    SC_SCAN_TYPE_PERIODIC = 0  # Scan window < scan interval => periodic scanning
    SC_SCAN_TYPE_CONTINUOUS = 1  # Scan window = scan interval => continuous scanning


class BLEScanner():
    def ble_e_model_sc_get_charge_scan_event(self, scan_window, event_type, scan_type, n_bytes_adv_ind, n_bytes_tx,
                                             n_bytes_rx,
                                             reception_after_time):
        """
        Calculates the charge consumed by a scan event.
        This function calculates the charge consumed by a scan event. Different event types are supported.
        Further, it is distinguished between continuous scanning and periodic scanning. For periodic scanning,
        each event begins with preprocessing and ends with postprocessing.
        For continuous scanning, no beginning and end can be distinguished.
        Therefore, the event duration is determined by definition: The event begins when a scanner begins scanning on a
        certain channel and ends with the end of the channel-changing to the next channel.
        Therefore, each scan event contains on channel-changing phase.
        :param: scanWindow	Scan window [s]. for SC_EVENT_TYPE_CON_REQ_OFFSET, this parameter is discarded
        :param: eventType	Type of the scan event that occurs.
        :param: scanType	Determines weather periodic scanning (scan window < scan interval) or
        continuous scanning (scan window = scan interval) takes place.
        :param: nBytesAdvInd	Bytes of the ADV_IND packet received.
        This value is currently ignored, it may be set to any value. It is reserved for future use.
        :param: nBytesTx	Number of bytes sent in a scan request or connection request packet by the master .
        Only used for \ref SC_EVENT_TYPE_ACTIVE_SCANNING, \ref SC_EVENT_TYPE_CON_REQ and \ref SC_EVENT_TYPE_CON_REQ_OFFSET
        :param: nBytesRx	Number of bytes received in a scan response. Only used for \ref SC_EVENT_TYPE_ACTIVE_SCANNING .
        :param: receptionAfterTime	Number of seconds beginning from the scan event after which
        an advertising packet has been received completely. As this value is unknown most times,
        the beginning of the reception can be inserted
        :return:Charge consumed by the scan event [As]
        """
        # Charge for pre- and postprocessing
        charge = BLE_E_MOD_SCAN_DPRE * BLE_E_MOD_SCAN_IPRE + BLE_E_MOD_SCAN_DPOST * BLE_E_MOD_SCAN_IPOST

        # Continuous scanning? => overwrite charge for pre-postprocessing with the charge for one channel-changing phase
        charge = BLE_E_MOD_SCAN_DCHCH * BLE_E_MOD_SCAN_ICHCH

        if event_type == BLEModelSCEventType.SC_EVENT_TYPE_NO_RECEPTION:
            charge += (scan_window + BLE_E_MOD_SCAN_DWOFFSET) * BLE_E_MOD_SCAN_IRX

        elif event_type == BLEModelSCEventType.SC_EVENT_TYPE_ABORTED:
            if scan_window < reception_after_time:
                charge += (scan_window + BLE_E_MOD_SCAN_DWOFFSET) * BLE_E_MOD_SCAN_IRX
            else:
                charge += (reception_after_time + BLE_E_MOD_SCAN_DWOFFSET) * BLE_E_MOD_SCAN_IRX

        elif event_type == BLEModelSCEventType.SC_EVENT_TYPE_PASSIVE_SCANNING:
            charge += (scan_window + BLE_E_MOD_SCAN_DWOFFSET) * BLE_E_MOD_SCAN_IRX

        elif event_type == BLEModelSCEventType.SC_EVENT_TYPE_ACTIVE_SCANNING:
            charge += (scan_window + BLE_E_MOD_SCAN_DWOFFSET - BLE_E_MOD_SCAN_DRXTX - BLE_E_MOD_SCAN_DPRETX -
                       8e-6 * n_bytes_tx - BLE_E_MOD_SCAN_DTXRX - BLE_E_MOD_SCAN_DPRERX - 8e-6 * n_bytes_rx -
                       BLE_E_MOD_SCAN_DRXRX) * BLE_E_MOD_SCAN_IRX + BLE_E_MOD_SCAN_DRXTX * BLE_E_MOD_SCAN_IRXTX + (
                              BLE_E_MOD_SCAN_DPRETX + 8e-6 * n_bytes_tx) * BLE_E_MOD_SCAN_ITX + BLE_E_MOD_SCAN_DTXRX * BLE_E_MOD_SCAN_ITXRX + (
                              BLE_E_MOD_SCAN_DPRERX + 8e-6 * n_bytes_rx) * BLE_E_MOD_SCAN_IRXS + BLE_E_MOD_SCAN_DRXRX * BLE_E_MOD_SCAN_IRXRX + BLE_E_MOD_SCAN_QCRX + BLE_E_MOD_SCAN_QCTX

        elif event_type == BLEModelSCEventType.SC_EVENT_TYPE_CON_REQ:
            charge += (
                              scan_window - reception_after_time) * BLE_E_MOD_SCAN_IRX + BLE_E_MOD_SCAN_DRXTX * BLE_E_MOD_SCAN_IRXTX + (
                              BLE_E_MOD_SCAN_DPRETX + 8e-6 * n_bytes_tx) * BLE_E_MOD_SCAN_ITX + BLE_E_MOD_SCAN_QCTX

        elif event_type == BLEModelSCEventType.SC_EVENT_TYPE_CON_REQ_OFFSET:
            # note: 'charge =' instead of 'charge +=' means: no pre- or postprocessing
            charge = (BLE_E_MOD_SCAN_DRXTX * BLE_E_MOD_SCAN_IRXTX + (
                    BLE_E_MOD_SCAN_DPRETX + 8e-6 * n_bytes_tx) * BLE_E_MOD_SCAN_ITX)

        return charge
