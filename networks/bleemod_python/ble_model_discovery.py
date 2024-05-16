import math

from networks.bleemod_python.ble_model_scanning import *
from networks.bleemod_python.ble_model_connected import BLEConnected
from networks.bleemod_python.ble_model_scanning import BLEScanner

'''
Call ble_model_discovery_getResult() to get an estimate for the device-discovery latency and the corresponding energies
spent by the master and  the slave. This function requires high amounts of computational power. 
Set the parameters, especially nPoints, maxTime and epsilonHit carefully. 
You probably don't want to use this function for online power management as it is computationally expensive.
'''


class DiscoveryModelResult:
    """
    Class to store the device discovery model results.
    """
    def __init__(self):
        # Result of the model for device discovery.
        self.chargeAdv = 0  # The charge consumed by the advertiser for device discovery [As]
        self.chargeScan = 0  # The charge consumed by the scanner for device discovery [As]
        self.discoveryLatency = 0  # The discovery latency [s]


class BLEDiscovery:
    """
    BLE device discovery implementation.
    """
    def _ble_model_discovery_normcdf(self, x, mu, sigma):
        """
        Calculates cumulative density function (CDF) of a (mu, sigma)-normal distribution by transforming the Gaussian CDF
        For the math behind this transformation, see http://en.wikipedia.org/wiki/Normal_distribution
        :param x: Value to evaluate
        :param mu: Mean value of the distribution
        :param sigma: Standard deviation of the distribution
        :return: Value of the CDF evaluated at x
        """
        return self._ble_model_discovery_gausscdf((x - mu) / sigma)

    def _ble_model_discovery_gausscdf(self, x):
        """
        Gaussian cumulative distribution function (CDF)
        :param x:
        :return:
        """
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        sign = 1
        if x < 0:
            sign = -1
        x = abs(x) / math.sqrt(2.0)

        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
        return 0.5 * (1.0 + sign * y)

    def _ble_model_discovery_get_approx_probab(self, mu, n, sigma, t, Ta_ideal, rho_max):
        """
        Computes the approximate probability of an advertising event having started before time t
        :param mu: Mean value of the starting time of the advertising event (=TaReal)
        :param n: Number of the advertising event. 0 => The event right after phi.
        1=> Event after one advertising interval, 2=> Event after two advertising intervals
        :param sigma:	Standard deviation of the starting time of the advertising event
        :param t:	Time to evaluate the CDF
        :param Ta_ideal: Ideal point in time the advertising event  starts(when no random advertising delay would exist)
        :param rho_max: Maximum random advDelay
        :return: Approximate probability that the advertising event starts before t
        """
        if n == 0:
            return 0 if t < Ta_ideal else 1
        elif n == 1:
            if Ta_ideal < t < Ta_ideal + rho_max:
                return (t - Ta_ideal) / rho_max
            elif t < Ta_ideal:
                return 0
            else:
                return 1
        elif n == 2:
            if t >= Ta_ideal:
                if Ta_ideal < t < Ta_ideal + rho_max:
                    return (t - Ta_ideal) * (t - Ta_ideal) / (2.0 * rho_max * rho_max)
                elif t < Ta_ideal + 2.0 * rho_max:
                    return 1 - (Ta_ideal + 2.0 * rho_max - t) * (Ta_ideal + 2.0 * rho_max - t) / (
                            2.0 * rho_max * rho_max)
                else:
                    return 1
            else:
                return 0
        else:
            return self._ble_model_discovery_normcdf(t, mu, sigma)

    def _ble_model_discovery_get_result_one_phi(self, epsilon_hit, Ta, Ts, ds, phi, rho_max, max_time):
        """
        Returns the model results (discovery-latency and discover-energy both for advertiser and scanner)
        for a given value offset phi
        :param epsilon_hit: The hit probability of all advertising events examined.
        As soon as the algorithm has reached this probability, it will consider the results as stable and stop.
        The closer this value becomes to one, the more precise the results become,
        but the algorithm takes longer as more advertising events are examined.
        Example: The first advertising event hits with probability 0.5, the second with 0.25 and the third with 0.15.
        The hit probability would be 0.5+0.25+0.15 = 0.9
        If epsilonHit is 0.89, the algorithm would end after three advertising events
        :param Ta: Advertising interval [s]
        :param Ts: Scan interval [s]
        :param ds: Scan window [s]
        :param phi: Offset of the first scan event (n=0) from the beginning of the scanning process
        :param rho_max: Maximum advertising delay [s]. Should be 10 ms according to the BLE specification
        :param max_time: The maximum discovery latency possible. After that, the algorithm stops due to performance reasons
        :return: Discovery latency and the discovery energy spent by the advertiser and the scanner
        """
        result = DiscoveryModelResult()
        result.chargeAdv = 0
        result.chargeScan = 0
        result.discoveryLatency = 0

        n = 0
        p_hit = 0
        p_cumm_miss = 1
        t_exp = 0
        charge_adv_exp = 0
        charge_scan_exp = 0
        current_t = 0
        channel = 0
        Ta_ideal = 0
        Ta_real = 0
        d_early = 0
        d_late = 0
        k = 0
        k_min = 0
        k_max = 0
        n_scan_events_before_advertising = 0
        scan_energy_before_advertising = 0
        scan_time_on_edge = 0
        scan_energy_on_edge = 0
        time_left = 0
        p_k = 0

        ble_connected = BLEConnected()
        t39_idle = ble_connected.ble_e_model_c_get_duration_event_same_payload(1, 0, 3, 0, BLE_E_MOD_CE_ADV_IND_PKG_LEN,
                                                                               3)
        q39_idle = ble_connected.ble_e_model_c_get_charge_event_same_payload(1, 0, 3, 0, BLE_E_MOD_CE_ADV_IND_PKG_LEN,
                                                                             3)

        q37 = ble_connected.ble_e_model_c_get_charge_event_same_payload(1, 0, 1, BLE_E_MOD_CE_CON_REQ_LEN,
                                                                        BLE_E_MOD_CE_ADV_IND_PKG_LEN,
                                                                        3)
        q38 = ble_connected.ble_e_model_c_get_charge_event_same_payload(1, 0, 2, BLE_E_MOD_CE_CON_REQ_LEN,
                                                                        BLE_E_MOD_CE_ADV_IND_PKG_LEN,
                                                                        3)
        q39 = ble_connected.ble_e_model_c_get_charge_event_same_payload(1, 0, 3, BLE_E_MOD_CE_CON_REQ_LEN,
                                                                        BLE_E_MOD_CE_ADV_IND_PKG_LEN,
                                                                        3)

        ble_scan = BLEScanner()

        while (1 - p_cumm_miss < epsilon_hit) and (t_exp < max_time):
            Ta_ideal = phi + float(n) * Ta
            Ta_real = Ta_ideal + float(n) * rho_max / 2.0

            k_min = math.floor(Ta_ideal / Ts)
            k_max = math.floor((Ta_ideal + float(n) * rho_max) / Ts)

            p_hit = 0

            n_scan_events_before_advertising = math.floor(phi / Ts)
            scan_energy_before_advertising = (float(n_scan_events_before_advertising) *
                                              ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                            BLEModelSCEventType.SC_EVENT_TYPE_NO_RECEPTION,
                                                                                            BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                            0, 0, 0, 0.0))

            scan_time_on_edge = phi - float(n_scan_events_before_advertising) * Ts
            if scan_time_on_edge > ds:
                scan_energy_on_edge = 0
                scan_energy_before_advertising += ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                                BLEModelSCEventType.SC_EVENT_TYPE_NO_RECEPTION,
                                                                                                BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                                0, 0, 0, 0)
            else:
                scan_energy_on_edge = ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                    BLEModelSCEventType.SC_EVENT_TYPE_ABORTED,
                                                                                    BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                    0, 0,
                                                                                    0, scan_time_on_edge)
                scan_energy_before_advertising += ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                                BLEModelSCEventType.SC_EVENT_TYPE_ABORTED,
                                                                                                BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                                0, 0, 0,
                                                                                                ds - scan_time_on_edge)

            for k in range(k_min, k_max + 1):
                channel = 37 + k % 3

                if channel == 37:
                    d_early = 0
                    d_late = 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN
                elif channel == 38:
                    d_early = 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 150e-6
                    d_late = 2.0 * 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 150e-6
                elif channel == 39:
                    d_early = 2.0 * (8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 150e-6)
                    d_late = 3.0 * 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 2.0 * 150e-6
                else:
                    # Handle the case where the channel is not 37, 38, or 39
                    raise ValueError("Invalid channel value")

                p_k = self._ble_model_discovery_get_approx_probab(Ta_real, n, math.sqrt(float(n) / 12.0) * rho_max,
                                                                  float(k) * Ts + ds - d_late, Ta_ideal, rho_max) - \
                      self._ble_model_discovery_get_approx_probab(Ta_real, n, math.sqrt(float(n) / 12.0) * rho_max,
                                                                  float(k) * Ts - d_early, Ta_ideal, rho_max)

                p_hit += p_k

                if channel == 37:
                    current_t = float(n) * (Ta + rho_max / 2.0) + 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN
                elif channel == 38:
                    current_t = float(n) * (Ta + rho_max / 2.0) + 2.0 * 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 150e-6
                elif channel == 39:
                    current_t = float(n) * (
                            Ta + rho_max / 2.0) + 3.0 * 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 2.0 * 150e-6
                else:
                    # Handle the case where the channel is not 37, 38, or 39
                    raise ValueError("Invalid channel value")

                t_exp += p_cumm_miss * p_k * current_t

                if n >= 1:
                    charge_adv_exp += p_cumm_miss * p_k * (float(n) - 1) * q39_idle
                    charge_adv_exp += p_cumm_miss * p_k * (float(n) - 1) * (Ta - t39_idle) * BLE_E_MOD_G_ISL

                if channel == 37:
                    charge_adv_exp += p_cumm_miss * p_k * q37
                elif channel == 38:
                    charge_adv_exp += p_cumm_miss * p_k * q38
                elif channel == 39:
                    charge_adv_exp += p_cumm_miss * p_k * q39
                else:
                    # Handle the case where the channel is not 37, 38, or 39
                    raise ValueError("Invalid channel value")

                n_full_scan_events = math.floor((current_t + phi) / Ts)
                time_left = (phi + current_t) - n_full_scan_events * Ts
                charge_scan_exp += p_cumm_miss * p_k * float(n_full_scan_events) * \
                                   ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                 BLEModelSCEventType.SC_EVENT_TYPE_NO_RECEPTION,
                                                                                 BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                 0, 0, 0,
                                                                                 0)
                if time_left > ds:
                    charge_scan_exp += p_cumm_miss * p_k * ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                                         BLEModelSCEventType.SC_EVENT_TYPE_NO_RECEPTION,
                                                                                                         BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                                         0, 0, 0, 0)
                else:
                    charge_scan_exp += ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                     BLEModelSCEventType.SC_EVENT_TYPE_ABORTED,
                                                                                     BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                     0, 0, 0, time_left)

            p_cumm_miss *= (1 - p_hit)

            if t_exp > max_time:
                t_exp = max_time
                break

            n += 1

        if t_exp > max_time:
            t_exp = max_time

        result.discoveryLatency = t_exp
        result.chargeAdv = charge_adv_exp
        result.chargeScan = charge_scan_exp - scan_energy_before_advertising
        return result

    def _ble_model_discovery_get_result_one_phi_alanezi(self, epsilon_hit, Ta, Ts, ds, phi, rho_max, max_time, n_bytes_tx):
        """
        Overloaded method to account for user and IoT privacy policies in the scanning/advertisement.
        Overloaded to support Alanezi work.
        Returns the model results (discovery-latency and discover-energy both for advertiser and scanner)
        for a given value offset phi
        :param epsilon_hit: The hit probability of all advertising events examined.
        As soon as the algorithm has reached this probability, it will consider the results as stable and stop.
        The closer this value becomes to one, the more precise the results become,
        but the algorithm takes longer as more advertising events are examined.
        Example: The first advertising event hits with probability 0.5, the second with 0.25 and the third with 0.15.
        The hit probability would be 0.5+0.25+0.15 = 0.9
        If epsilonHit is 0.89, the algorithm would end after three advertising events
        :param Ta: Advertising interval [s]
        :param Ts: Scan interval [s]
        :param ds: Scan window [s]
        :param phi: Offset of the first scan event (n=0) from the beginning of the scanning process
        :param rho_max: Maximum advertising delay [s]. Should be 10 ms according to the BLE specification
        :param max_time: The maxmimum discovery latency possible. After that, the algorithm stops due to performance reasons
        :param n_bytes_tx: Number of bytes sent in a scan request or connection request packet by the master .
        Only used for \ref SC_EVENT_TYPE_ACTIVE_SCANNING, \ref SC_EVENT_TYPE_CON_REQ and \ref SC_EVENT_TYPE_CON_REQ_OFFSET
        :return: Discovery latency and the discovery energy spent by the advertiser and the scanner
        """
        result = DiscoveryModelResult()
        result.chargeAdv = 0
        result.chargeScan = 0
        result.discoveryLatency = 0

        n = 0
        p_hit = 0
        p_cumm_miss = 1
        t_exp = 0
        charge_adv_exp = 0
        charge_scan_exp = 0
        current_t = 0
        channel = 0
        Ta_ideal = 0
        Ta_real = 0
        d_early = 0
        d_late = 0
        k = 0
        k_min = 0
        k_max = 0
        n_scan_events_before_advertising = 0
        scan_energy_before_advertising = 0
        scan_time_on_edge = 0
        scan_energy_on_edge = 0
        time_left = 0
        p_k = 0

        ble_connected = BLEConnected()
        # Added n_bytes_tx to the BLE_E_MOD_CE_ADV_IND_PKG_LEN, since the advertiser
        # (user) in Alanezi includes its PP/request to access the IoT resources
        t39_idle = ble_connected.ble_e_model_c_get_duration_event_same_payload(1, 0, 3, 0,
                                                                               BLE_E_MOD_CE_ADV_IND_PKG_LEN + n_bytes_tx,
                                                                               3)
        q39_idle = ble_connected.ble_e_model_c_get_charge_event_same_payload(1, 0, 3, 0,
                                                                             BLE_E_MOD_CE_ADV_IND_PKG_LEN + n_bytes_tx,
                                                                             3)

        q37 = ble_connected.ble_e_model_c_get_charge_event_same_payload(1, 0, 1, BLE_E_MOD_CE_CON_REQ_LEN,
                                                                        BLE_E_MOD_CE_ADV_IND_PKG_LEN + n_bytes_tx,
                                                                        3)
        q38 = ble_connected.ble_e_model_c_get_charge_event_same_payload(1, 0, 2, BLE_E_MOD_CE_CON_REQ_LEN,
                                                                        BLE_E_MOD_CE_ADV_IND_PKG_LEN + n_bytes_tx,
                                                                        3)
        q39 = ble_connected.ble_e_model_c_get_charge_event_same_payload(1, 0, 3, BLE_E_MOD_CE_CON_REQ_LEN,
                                                                        BLE_E_MOD_CE_ADV_IND_PKG_LEN + n_bytes_tx,
                                                                        3)

        ble_scan = BLEScanner()

        while (1 - p_cumm_miss < epsilon_hit) and (t_exp < max_time):
            Ta_ideal = phi + float(n) * Ta
            Ta_real = Ta_ideal + float(n) * rho_max / 2.0

            k_min = math.floor(Ta_ideal / Ts)
            k_max = math.floor((Ta_ideal + float(n) * rho_max) / Ts)

            p_hit = 0

            n_scan_events_before_advertising = math.floor(phi / Ts)
            scan_energy_before_advertising = (float(n_scan_events_before_advertising) *
                                              ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                            BLEModelSCEventType.SC_EVENT_TYPE_NO_RECEPTION,
                                                                                            BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                            0, 0, 0, 0.0))

            scan_time_on_edge = phi - float(n_scan_events_before_advertising) * Ts
            if scan_time_on_edge > ds:
                scan_energy_on_edge = 0
                scan_energy_before_advertising += ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                                BLEModelSCEventType.SC_EVENT_TYPE_NO_RECEPTION,
                                                                                                BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                                0, 0, 0, 0)
            else:
                scan_energy_on_edge = ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                    BLEModelSCEventType.SC_EVENT_TYPE_ABORTED,
                                                                                    BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                    0, 0,
                                                                                    0, scan_time_on_edge)
                scan_energy_before_advertising += ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                                BLEModelSCEventType.SC_EVENT_TYPE_ABORTED,
                                                                                                BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                                0, 0, 0,
                                                                                                ds - scan_time_on_edge)

            for k in range(k_min, k_max + 1):
                channel = 37 + k % 3

                if channel == 37:
                    d_early = 0
                    d_late = 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN
                elif channel == 38:
                    d_early = 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 150e-6
                    d_late = 2.0 * 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 150e-6
                elif channel == 39:
                    d_early = 2.0 * (8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 150e-6)
                    d_late = 3.0 * 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 2.0 * 150e-6
                else:
                    # Handle the case where the channel is not 37, 38, or 39
                    raise ValueError("Invalid channel value")

                p_k = self._ble_model_discovery_get_approx_probab(Ta_real, n, math.sqrt(float(n) / 12.0) * rho_max,
                                                                  float(k) * Ts + ds - d_late, Ta_ideal, rho_max) - \
                      self._ble_model_discovery_get_approx_probab(Ta_real, n, math.sqrt(float(n) / 12.0) * rho_max,
                                                                  float(k) * Ts - d_early, Ta_ideal, rho_max)

                p_hit += p_k

                if channel == 37:
                    current_t = float(n) * (Ta + rho_max / 2.0) + 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN
                elif channel == 38:
                    current_t = float(n) * (Ta + rho_max / 2.0) + 2.0 * 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 150e-6
                elif channel == 39:
                    current_t = float(n) * (
                            Ta + rho_max / 2.0) + 3.0 * 8e-6 * BLE_E_MOD_CE_ADV_IND_PKG_LEN + 2.0 * 150e-6
                else:
                    # Handle the case where the channel is not 37, 38, or 39
                    raise ValueError("Invalid channel value")

                t_exp += p_cumm_miss * p_k * current_t

                if n >= 1:
                    charge_adv_exp += p_cumm_miss * p_k * (float(n) - 1) * q39_idle
                    charge_adv_exp += p_cumm_miss * p_k * (float(n) - 1) * (Ta - t39_idle) * BLE_E_MOD_G_ISL

                if channel == 37:
                    charge_adv_exp += p_cumm_miss * p_k * q37
                elif channel == 38:
                    charge_adv_exp += p_cumm_miss * p_k * q38
                elif channel == 39:
                    charge_adv_exp += p_cumm_miss * p_k * q39
                else:
                    # Handle the case where the channel is not 37, 38, or 39
                    raise ValueError("Invalid channel value")

                n_full_scan_events = math.floor((current_t + phi) / Ts)
                time_left = (phi + current_t) - n_full_scan_events * Ts
                charge_scan_exp += p_cumm_miss * p_k * float(n_full_scan_events) * \
                                   ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                 BLEModelSCEventType.SC_EVENT_TYPE_NO_RECEPTION,
                                                                                 BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                 0, 0, 0,
                                                                                 0)
                if time_left > ds:
                    charge_scan_exp += p_cumm_miss * p_k * ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                                         BLEModelSCEventType.SC_EVENT_TYPE_NO_RECEPTION,
                                                                                                         BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                                         0, 0, 0, 0)
                else:
                    charge_scan_exp += ble_scan.ble_e_model_sc_get_charge_scan_event(ds,
                                                                                     BLEModelSCEventType.SC_EVENT_TYPE_ABORTED,
                                                                                     BLEModelSCScanType.SC_SCAN_TYPE_PERIODIC,
                                                                                     0, 0, 0, time_left)

            p_cumm_miss *= (1 - p_hit)

            if t_exp > max_time:
                t_exp = max_time
                break

            n += 1

        if t_exp > max_time:
            t_exp = max_time

        result.discoveryLatency = t_exp
        result.chargeAdv = charge_adv_exp
        result.chargeScan = charge_scan_exp - scan_energy_before_advertising
        return result

    def ble_model_discovery_get_result(self, n_points, epsilon_hit, Ta, Ts, ds, rho_max, max_time):
        """
        Returns the model results (discovery-latency and discover-energy both for advertiser and scanner)
        for varying advertising offsets phi. nPoints different values of phi are examined.
        :param n_points: Number of advertising events phi to be examined.
        The higher, the better the accuracy becomes but the longer the computation takes.
        :param epsilon_hit: The hit probability of all advertising events examined for a particular phi.
        As soon as the algorithm has reached this probability, it will consider the results as stable and stop.
        The closer this value becomes to one, the more precise the results become, but the algorithm takes longer
        as more advertising events are examined.
        Example: The first advertising event hits with probability 0.5, the second with 0.25 and the third with 0.15.
        The hit probability would be 0.5+0.25+0.15 = 0.9
        If epsilonHit is 0.89, the algorithm would end after three advertising events
        :param Ta: Advertising interval [s]
        :param Ts: Scan interval [s]
        :param ds: Scan window [s]
        :param rho_max: Maximum advertising delay [s]. Should be 10 ms according to the BLE specification
        :param max_time: The maxmimum discovery latency possible. After that, the algorithm stops due to performance reasons
        :return: Discovery latency and the discovery energy spent by the advertiser and the scanner
        """
        delta = (3.0 * Ts) / float(n_points)
        phi = 0
        result_single = DiscoveryModelResult()
        result_joined = DiscoveryModelResult()
        result_joined.chargeAdv = 0
        result_joined.chargeScan = 0
        result_joined.discoveryLatency = 0

        for cnt in range(n_points):
            result_single = self._ble_model_discovery_get_result_one_phi(epsilon_hit, Ta, Ts, ds, phi, rho_max,
                                                                         max_time)
            result_joined.discoveryLatency += result_single.discoveryLatency
            result_joined.chargeAdv += result_single.chargeAdv
            result_joined.chargeScan += result_single.chargeScan
            phi += delta

        result_joined.discoveryLatency /= float(n_points)
        result_joined.chargeAdv /= float(n_points)
        result_joined.chargeScan /= float(n_points)
        return result_joined

    def ble_model_discovery_get_result_alanezi(self, n_points, epsilon_hit, Ta, Ts, ds, rho_max, max_time, n_bytes_tx):
        """
            Overloaded to account for Alanezi!
            Returns the model results (discovery-latency and discover-energy both for advertiser and scanner)
            for varying advertising offsets phi. nPoints different values of phi are examined.
            :param n_points: Number of advertising events phi to be examined.
            The higher, the better the accuracy becomes but the longer the computation takes.
            :param epsilon_hit: The hit probability of all advertising events examined for a particular phi.
            As soon as the algorithm has reached this probability, it will consider the results as stable and stop.
            The closer this value becomes to one, the more precise the results become, but the algorithm takes longer
            as more advertising events are examined.
            Example: The first advertising event hits with probability 0.5, the second with 0.25 and the third with 0.15.
            The hit probability would be 0.5+0.25+0.15 = 0.9
            If epsilonHit is 0.89, the algorithm would end after three advertising events
            :param Ta: Advertising interval [s]
            :param Ts: Scan interval [s]
            :param ds: Scan window [s]
            :param rho_max: Maximum advertising delay [s]. Should be 10 ms according to the BLE specification
            :param max_time: The maximum discovery latency possible. After that, the algorithm stops due to performance reasons
            :param n_bytes_tx: Privacy policy bytes to include in the advertisement/broadcast
            :return: Discovery latency and the discovery energy spent by the advertiser and the scanner
            """
        delta = (3.0 * Ts) / float(n_points)
        phi = 0
        result_single = DiscoveryModelResult()
        result_joined = DiscoveryModelResult()
        result_joined.chargeAdv = 0
        result_joined.chargeScan = 0
        result_joined.discoveryLatency = 0

        for cnt in range(n_points):
            result_single = self._ble_model_discovery_get_result_one_phi_alanezi(epsilon_hit, Ta, Ts, ds, phi, rho_max,
                                                                         max_time, n_bytes_tx)
            result_joined.discoveryLatency += result_single.discoveryLatency
            result_joined.chargeAdv += result_single.chargeAdv
            result_joined.chargeScan += result_single.chargeScan
            phi += delta

        result_joined.discoveryLatency /= float(n_points)
        result_joined.chargeAdv /= float(n_points)
        result_joined.chargeScan /= float(n_points)
        return result_joined
