from networks.bleemod_python.bleemod_python import BLEEMod


def main(test_or_config):
    """
    Used to validate the BLEEMod library and configure BLE model parameters.
    :param test_or_config: 0 for validating the library and 1 for configuring parameters
    """
    bleemod = BLEEMod()

    if not test_or_config:
        # Some examples in connected mode:
        # get the duration of all constant parts of a connection event. (Preprocessing, Postprocessing,...)
        dc = bleemod.connected.ble_e_model_c_get_duration_constant_parts()
        # get the duration of the connection sequence (all non-constant parts of the model)
        dseq = bleemod.connected.ble_e_model_c_get_duration_sequences_same_payload(1, 0.1, 5, 10, 22, 3)
        dwhole = bleemod.connected.ble_e_model_c_get_duration_event_same_payload(1, 0.1, 5, 10, 22, 3)

        # now do the same with the charge of these phases
        charge_c = bleemod.connected.ble_e_model_c_get_charge_constant_parts()
        charge_seq = bleemod.connected.ble_e_model_c_get_charge_sequences_same_payload(1, 0.1, 5, 10, 22, 3)
        charge_whole = bleemod.connected.ble_e_model_c_get_charge_event_same_payload(1, 0.1, 5, 10, 22, 3)

        print(f"Duration: const {dc} - seq: {dseq}, whole: {dwhole}")
        print(f"Charge: const {charge_c} - seq: {charge_seq}, whole: {charge_whole}")

        # now we're not interested in the events only, but also in the sleeping phase of a connection event
        charge_interval = bleemod.connected.ble_e_model_c_get_charge_connection_interval_same_payload(0, 0.1, 5, 10, 22,
                                                                                                      3)
        print(f"Charge for connection interval: {charge_interval}")

        # now get the charge for a master establishing a connection.
        # We are only interested in the additional energy that
        # is not accounted for in the energy model for device discovery as described in the paper,
        # and not the whole model.
        # Therefore, we use \ref SC_EVENT_TYPE_CON_REQ_OFFSET
        cro_charge = (bleemod.scanner.ble_e_model_sc_get_charge_scan_event
                      (0.025, 6, 0, 37, 44, 0,
                       0.125))  # Using the values directly, # adjust if needed
        print(f"Connection Request offset charge: {cro_charge}")

        # now we calculate the energy consumption of a scan event with active scanning that receives and
        # replies to an advertising event
        cro_act_scan = (bleemod.scanner.ble_e_model_sc_get_charge_scan_event
                        (0.025, 2, 0, 28, 22, 34, 0.125))  # Using the values directly, adjust if needed
        print(f"Active Scanning Event: {cro_act_scan}")

        # Calculate the latency and energy consumption of device discovery for Ta = 2.55s, Ts = 2.56s and ds = 64ms.
        result = bleemod.discovery.ble_model_discovery_get_result(100, 0.9999, 2.55, 2.56, 0.064, 0.01, 1000)
        print(
            f"Discovery latency: {result.discoveryLatency}\tdiscovery energy: advertiser: {result.chargeAdv}, "
            f"scanner: {result.chargeScan}")

        # The results must align with the reference library implementation results. Output of the original library:
        # Duration: const 0.001962000000000 - seq: 0.002765000000000, whole: 0.004727000000000
        # Charge: const 0.000014624297000 - seq: 0.000071463685000, whole: 0.000086087982000
        # Charge for connection interval: 0.000093730449500
        # Connection Request offset charge: 0.000014901899000
        # Active Scanning Event: 0.000615441259000
        # discovery latency: 583.055109502707069
        # discovery energy: advertiser: 0.015175933492857, scanner: 0.393044409090591

    else:
        # Use this portion of the code to test the configuration of advertising and scanning parameters and its effects
        # on the output of the energy model.
        # We use
        # https://www.researchgate.net/publication/335808941_Connection-less_BLE_Performance_Evaluation_on_Smartphones
        # as a reference for realistic values
        total_user_power_consumption = 0
        total_owner_power_consumption = 0

        charge_c = bleemod.connected.ble_e_model_c_get_charge_constant_parts()
        print("Charge Const: ", charge_c)

        total_user_power_consumption += charge_c
        total_owner_power_consumption += charge_c

        result = bleemod.discovery.ble_model_discovery_get_result_alanezi(100, 0.9999, 0.25, 5, 2, 0.01, 1000, 217)

        total_user_power_consumption += result.chargeAdv
        total_owner_power_consumption += result.chargeScan

        print("Scan duration: ", result.discoveryLatency)

        print("User advertisement charge: ", result.chargeAdv)
        print("Owner scan charge: ", result.chargeScan)

        result = (
            bleemod.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
            (1, 0, 1,
             0,
             0.1))
        print("User ce charge: ", result)
        result = (
            bleemod.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
            (1, 0, 0,
             0,
             0.1))
        print("Owner ce charge: ", result)


if __name__ == "__main__":
    test_or_config = 0  # 0 test and 1 config
    main(test_or_config)
