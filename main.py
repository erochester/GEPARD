from user import *
import numpy as np
import random
import math
import logging
import sys

from shopping_mall import ShoppingMall
from iot_device import IoTDevice
from negotiation import NegotiationProtocol
from driver import Driver
from util import check_distance
from network import Network


def lora(user_pp_size, owner_pp_size, user_consent):
    voltage = 3.3
    i_rx = 11.2
    cr = 4 / 5

    # the pp size determines the mode we will use
    if max(user_pp_size, owner_pp_size) <= 51:
        lora_max_payload = 51
        sf = 10
        bw = 250
        i_tx = 125
    elif 51 < max(user_pp_size, owner_pp_size) <= 115:
        lora_max_payload = 115
        sf = 9
        bw = 250
        i_tx = 90
    else:
        lora_max_payload = 242
        sf = 7
        bw = 500
        i_tx = 28

    user_pp_packets = math.ceil(user_pp_size / lora_max_payload)
    owner_pp_packets = math.ceil(owner_pp_size / lora_max_payload)

    total_user_power_consumption = 0
    total_owner_power_consumption = 0

    # distance formula np.sqrt((curr_loc[0]**2+curr_loc[1]**2))

    # assume same pre- and post-processing power consumption for LoRa and BLE
    # now we iterate through user consent and sum up the power consumption
    for u in user_consent:
        # check how many phases in negotiation
        # if 0 we don't do anything
        # if 1 phase
        t_tx_user = 0
        t_tx_owner = 0
        if u == 1:
            # the user sends the PP to the owner
            # calculate the amount of time it takes to do it
            if user_pp_packets <= 1:
                t_sym = (2 ** sf) / bw
                t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
                n_phy = 8 + max(math.ceil((28 + 8 * user_pp_size + 4 * sf) / (4 * sf)) * (cr + 4), 0)
                t_phy = t_sym * n_phy
                t_tx_user = t_pre + t_phy

            if owner_pp_packets <= 1:
                t_sym = (2 ** sf) / bw
                t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
                n_phy = 8 + max(math.ceil((28 + 8 * owner_pp_size + 4 * sf) / (4 * sf)) * (cr + 4), 0)
                t_phy = t_sym * n_phy
                t_tx_owner = t_pre + t_phy

            # does it fit into 1 packet?
            if user_pp_packets > 1:
                t_sym = (2 ** sf) / bw
                t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
                n_phy = 8 + max(math.ceil((28 + 8 * (user_pp_size - lora_max_payload) + 4 * sf) / (4 * sf)) * (cr + 4),
                                0)
                t_phy = t_sym * n_phy
                t_temp_tx = t_pre + t_phy
                t_tx_user = t_temp_tx

                n_phy = 8 + max(math.ceil((28 + 8 * lora_max_payload + 4 * sf) / (4 * sf)) * (cr + 4), 0)
                t_phy = t_sym * n_phy
                t_temp_tx = t_pre + t_phy
                t_tx_user += t_temp_tx

            if owner_pp_packets > 1:
                t_sym = (2 ** sf) / bw
                t_pre = t_sym * 4.25  # assume N_pre = 0 and crc = 0
                n_phy = 8 + max(math.ceil((28 + 8 * lora_max_payload + 4 * sf) / (4 * sf)) * (cr + 4), 0)
                t_phy = t_sym * n_phy
                t_temp_tx = t_pre + t_phy
                t_tx_owner = t_temp_tx

                n_phy = 8 + max(math.ceil((28 + 8 * (owner_pp_size - lora_max_payload) + 4 * sf) / (4 * sf)) * (cr + 4),
                                0)
                t_phy = t_sym * n_phy
                t_temp_tx = t_pre + t_phy
                t_tx_owner += t_temp_tx

            # it will take user_pp_packets tranmissions on the IoT user side
            total_user_power_consumption += t_tx_user * voltage * i_tx

            # the owner accepts the PP and starts "relaying" the data or
            # collecting the data, as such the negotiation is done
            total_owner_power_consumption += t_tx_user * voltage * i_rx

        # if negotiation is 2 phases
        elif u == 2:
            # in 2 phase negotiation we start exactly the same way as in 1 phase
            # the user sends the PP to the owner
            # it will take user_pp_packets tranmissions on the IoT user side
            total_user_power_consumption += t_tx_user * voltage * i_tx

            # the owner accepts doesnt accept the PP
            total_owner_power_consumption += t_tx_user * voltage * i_rx

            # following that, however, the owner sends a different proposal
            total_owner_power_consumption += t_tx_owner * voltage * i_rx

            # user receives the owner pp
            total_user_power_consumption += t_tx_owner * voltage * i_rx

            # the user then sends the reply
            total_user_power_consumption += t_tx_user * voltage * i_tx

            # owner receives it
            total_owner_power_consumption += t_tx_user * voltage * i_rx

    return total_user_power_consumption, total_owner_power_consumption


def ble_cunche(user_pp_size, owner_pp_size, user_consent):
    # BLE power consumption calculations
    # FIXME: later we put into a separate module to be able to easily exchange the protocols
    # BLE max payload size is 251 bytes, so we calculate the number of packets
    ble_max_payload = 251
    user_pp_packets = math.ceil(user_pp_size / ble_max_payload)
    owner_pp_packets = math.ceil(owner_pp_size / ble_max_payload)

    total_user_power_consumption = 0
    total_owner_power_consumption = 0

    # tx power consumption is 84mW
    tx_power_consumption = 84

    # rx power consumption is 66mW
    rx_power_consumption = 66

    # in between packet wait time power consumption is 45mW
    ifs_power_consumption = 45

    # Processing power consumption values change according to the processing done
    # pre-processing power consumption is 15mW
    pre_power_consumption = 15

    # post-processing power consumption is 24mW
    post_power_consumption = 24

    # now we iterate through user consent and sum up the power consumption
    for u in user_consent:
        # check how many phases in negotiation
        # if 0 we don't do anything
        # if 1 phase
        if u == 1:
            # the owner sends the PP to the user
            # it will take owner_pp_packets tranmissions on the IoT user side
            total_owner_power_consumption += pre_power_consumption + owner_pp_packets * tx_power_consumption + \
                                             (owner_pp_packets - 1) * ifs_power_consumption + post_power_consumption

            # the user receives the PP
            total_user_power_consumption += pre_power_consumption + owner_pp_packets * rx_power_consumption + \
                                            (owner_pp_packets - 1) * ifs_power_consumption + post_power_consumption

            # the user consents
            total_user_power_consumption += pre_power_consumption + user_pp_packets * tx_power_consumption + \
                                            (user_pp_packets - 1) * ifs_power_consumption + post_power_consumption

            # the owner receives consent
            total_owner_power_consumption += pre_power_consumption + user_pp_packets * rx_power_consumption + \
                                             (user_pp_packets - 1) * ifs_power_consumption + post_power_consumption

    return total_user_power_consumption, total_owner_power_consumption


def cunche(curr_users_list):
    user_consent = []

    user_pp_size = 38
    owner_pp_size = 86

    # remove users that are > x meters away from IoT device
    applicable_users = []
    distance = 40
    for u in curr_users_list:
        if check_distance(u.curr_loc, distance):
            applicable_users.append(u)

    for u in applicable_users:
        # check if user already consented and if not
        if not u.consent:
            # check the user's privacy label
            if u.privacy_label == 1:
                # for fundamentalists, we offer we see if user is in 79.6% non-consenting
                if random.random() <= 0.796:
                    u.updateConsent(True)
                    user_consent.append(1)
                else:
                    user_consent.append(0)
            # everyone else consents
            else:
                u.updateConsent(True)
                user_consent.append(1)

    # total_user_power_consumption, total_owner_power_consumption = \
    #     ble_cunche(user_pp_size, owner_pp_size, user_consent)
    total_user_power_consumption, total_owner_power_consumption = \
        lora(user_pp_size, owner_pp_size, user_consent)

    return user_consent, applicable_users, total_user_power_consumption, total_owner_power_consumption


def main():
    random.seed(123)

    algo = 1

    # create the scenario that determines user types, locations and movement patterns, network parameters and
    # simulation runtime
    list_of_users = []

    # initialize iot device
    iot_device = IoTDevice((0,0))

    # Generates the users/PAs
    scenario = ShoppingMall(list_of_users, iot_device)
    scenario.generate_scenario()

    # print list of users
    for u in list_of_users:
        print(u)

    # plot user locations
    # scenario.plot_scenario()

    # network technology that determines the range of communication, power consumed and allowed data rates
    network = Network("ble", logger)

    # create the negotiation protocol object that determines the rules of the encounter
    negotiation_protocol = NegotiationProtocol(algo, network, logger)

    driver = Driver(scenario, network, negotiation_protocol, logger)

    total_consented, total_user_power_consumption, total_owner_power_consumption, end_time = \
        driver.run()  # drives the simulation environment

    print("[!] Total User Power Consumption (mW): ", total_user_power_consumption)
    print("[!] Total Owner Power Consumption (mW): ", total_owner_power_consumption)
    print("[!] Consent collected from: ", total_consented)
    print("[!] Total user number: ", len(list_of_users))
    print("[!] Total runtime (s): ", round(end_time, 2))


if __name__ == "__main__":
    # Create and configure logger
    logging.basicConfig(filename="debug.log", format='%(asctime)s %(message)s', filemode='w')
    # Creating an object
    logger = logging.getLogger()

    # Setting the threshold of logger to DEBUG
    logger.setLevel(logging.DEBUG)

    main()
