from networks.bleemod_python.bleemod_python import BLEEMod

import matplotlib.pyplot as plt

def proposal_based_neg(payload, rate, ble):
    # Sending over 1 hour of packets from IoT device perspective
    # We assume 1 user per minute on average
    # Will send ~50% more packets than ABP as per Forst work
    # Each with discovery and connection establishment
    total_power_consumed = 0

    # 60 (1 user per minute for an hour) but + rate
    for i in range(0, 60+int(60*rate)):

        charge_c = ble.connected.ble_e_model_c_get_charge_constant_parts()

        total_power_consumed += charge_c

        result = ble.discovery.ble_model_discovery_get_result_alanezi(100, 0.9999, 0.25, 5, 2, 0.01, 1000, payload)

        total_power_consumed += result.chargeAdv

        result = (
            ble.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
            (1, 0, 0,
             0,
             0.1))

        total_power_consumed += result

    return total_power_consumed

def argument_based_neg(payload, ble):
    # Sending over 1 hour of packets from IoT device perspective
    # We assume 1 user per minute on average
    # Will send ~50% less packets than PBN as per Forst work
    # Each with discovery and connection establishment
    total_power_consumed = 0

    # 60 (1 user per minute for an hour)
    for i in range(0, 60):
        charge_c = ble.connected.ble_e_model_c_get_charge_constant_parts()

        total_power_consumed += charge_c

        result = ble.discovery.ble_model_discovery_get_result_alanezi(100, 0.9999, 0.25, 5, 2, 0.01, 1000, payload)

        total_power_consumed += result.chargeAdv

        result = (
            ble.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
            (1, 0, 0,
             0,
             0.1))

        total_power_consumed += result

    return total_power_consumed

if __name__ == "__main__":
    ble = BLEEMod()


    min_payload = 0
    max_payload = 650
    # max_payload = 200

    pbn_power_consumed = []
    abn_power_consumed = []
    pbn_25_power_consumed = []
    pbn_50_power_consumed = []
    abn_25_power_consumed = []
    abn_50_power_consumed = []

    x = range(min_payload,max_payload,25)

    for payload in x:
        print("Running for payload size: ", payload)
        # Baseline
        pbn_power_consumed.append(proposal_based_neg(payload, 0, ble))
        # Baseline
        abn_power_consumed.append(argument_based_neg(payload, ble))
        # Assumption is that packet rate is +25%
        pbn_25_power_consumed.append(proposal_based_neg(payload, 0.25, ble))
        # Assumption is that packet rate is +50%
        pbn_50_power_consumed.append(proposal_based_neg(payload, 0.5, ble))
        # Assumption is that for ABN metadata is no more than 25% of payload
        abn_25_power_consumed.append(argument_based_neg(payload+0.25*payload, ble))
        # Assumption is that for ABN metadata is no more than 50% of payload
        abn_50_power_consumed.append(argument_based_neg(payload + 0.5 * payload, ble))

    plt.plot(x, pbn_power_consumed, label="PBN", marker='d', ms=10)
    plt.plot(x, abn_power_consumed, label="ABN", marker = '^', ms=10)
    plt.plot(x, pbn_25_power_consumed, label="PBN_25", marker = 'x', ms=10)
    plt.plot(x, pbn_50_power_consumed, label="PBN_50", marker='v', ms=10)
    plt.plot(x, abn_25_power_consumed, label="ABN_25", marker = '+', ms=10)
    plt.plot(x, abn_50_power_consumed, label="ABN_50", marker='*', ms=10)

    plt.legend(loc='upper center', bbox_to_anchor=(0.5, 1.15),
          fancybox=True, shadow=True, ncol=5)
    # plt.grid(color = 'grey', linestyle = '--',)

    plt.xlabel("Payload size (Bytes)")
    plt.ylabel("Current consumption (A)")

    plt.show()