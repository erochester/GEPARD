import logging
import random
import sys

import numpy as np

from util import check_distance, calc_time_remaining, calc_utility


class Concession:
    """
    Implements Concession negotiation protocol. Includes BLE, ZigBee and LoRa based negotiations.
    """

    def __init__(self, network):
        """
        Initializes Concession class. Includes BLE, ZigBee and LoRa based negotiations.
        Also includes user_utility dictionary of user's utility where user's id is the key
        :param network: network type (e.g., BLE)
        """
        self.network = network
        self.user_utility = {}

    def run(self, curr_users_list, iot_device):
        """
        Main driver for the negotiations. Sets up the main parameter, determines applicable user set for the
        negotiations, calls multiprocessor to run the negotiation matching the network type selected and processes
        the results.
        :param curr_users_list: list of current users in the environment (Users object).
        :param iot_device: IoT device object.
        :return: Returns total device power and time consumption, as well as the updated user lists.
        """
        user_pp_size = 38
        owner_pp_size = 86

        # Create dictionary of user's utility where user's id is the key
        self.user_utility = {}

        # remove users that are > x meters away from IoT device
        applicable_users = []
        distance = self.network.network_impl.comm_distance
        for u in curr_users_list:
            if check_distance(u.curr_loc, distance) and not u.consent:
                applicable_users.append(u)

        for step in range(5):
            # check if there are still unconcented users and if not, exit negotiation
            unconcented_users = [u for u in applicable_users if not u.consent]

            if not unconcented_users:
                break

            # Empty the dictionary of user's utility
            self.user_utility = {}

            # Calculate utility for each unconcented user and add to dictionary
            for u in unconcented_users:
                self.calc_assumed_utility(u)

            # Sort the unconcented users dictionary based on their utility
            sorted_user_utility = sorted(self.user_utility.items(), key=lambda x: x[1], reverse=True)

            # Get the highest utility user given the user id
            highest_utility_user = [u for u in applicable_users if u.id_ == sorted_user_utility[0][0]][0]

            # Check the highest utility user's privacy label
            if highest_utility_user.privacy_label == 1:
                # for fundamentalists, we offer the minimum consent option
                if random.random() <= 0.2:
                    highest_utility_user.update_consent(1)
                    highest_utility_user.update_neg_attempted()
            # everyone else consents
            else:
                highest_utility_user.update_consent(1)
                highest_utility_user.update_neg_attempted()

            if highest_utility_user.consent:
                if self.network.network_type == "ble":
                    # Calculate the power consumption and duration for BLE
                    self.ble_negotiation(user_pp_size, owner_pp_size, highest_utility_user, iot_device)
                elif self.network.network_type == "zigbee":
                    # Calculate the power consumption and duration for zigbee
                    self.zigbee_negotiation(user_pp_size, owner_pp_size, highest_utility_user, iot_device)
                elif self.network.network_type == "lora":
                    # Calculate the power consumption and duration for zigbee
                    self.lora_negotiation(user_pp_size, owner_pp_size, highest_utility_user, iot_device)
                else:
                    # raise error and exit
                    logging.info("Invalid network type in concession.py.")
                    sys.exit(1)

                # Calculate user and owner utility
                highest_utility_user.add_to_utility(calc_utility(calc_time_remaining(highest_utility_user),
                                                                 highest_utility_user.power_consumed,
                                                                 highest_utility_user.weights))
                # Use the user remaining time to calculate the IoT device utility,
                # since the user is moving away (not the device)
                iot_device.add_to_utility(calc_utility(calc_time_remaining(highest_utility_user),
                                                       iot_device.power_consumed, iot_device.weights))
                if iot_device.utility == float("inf"):
                    # raise error and exit
                    logging.error("Got infinite utility for IoT device in cunche.py.")
                    sys.exit(-1)

    def calc_assumed_utility(self, user):
        """
        Calculate user's utility given how much longer the user stays in the environment
        :param user: User object under consideration.
        """

        # Get user id
        user_id = user.id_

        # Calculate time it takes for user to reach destination
        time = calc_time_remaining(user)

        # Calculate user's utility using exponential decay function
        utility = np.exp(-time)

        # Add user's utility to dictionary
        self.user_utility[user_id] = utility

    def ble_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        BLE-based Concession negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT Device.
        :return: Power and time consumption of user and iot device.
        """

        # has to be local not to double count
        iot_device_power_consumed = 0
        iot_device_time_consumed = 0

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u.consent:
            # get the duration of all constant parts of a connection event. (Preprocessing, Postprocessing,...)
            dc = self.network.network_impl.connected.ble_e_model_c_get_duration_constant_parts()

            # now do the same with the charge of these phases
            charge_c = self.network.network_impl.connected.ble_e_model_c_get_charge_constant_parts()

            # charge_c is in [C], so we should divide by dc to get the current
            current_c = charge_c / dc

            u.add_to_time_spent(dc)
            iot_device_time_consumed += dc
            u.add_to_power_consumed(current_c)
            iot_device_power_consumed += current_c

            # Calculate the latency and energy consumption of device discovery. The values are taken from:
            # https://www.researchgate.net/publication/335808941_Connection-less_BLE_Performance_Evaluation_on_Smartphones
            result = (self.network.network_impl.discovery.ble_model_discovery_get_result
                      (100, 0.9999, 0.25, 5, 2, 0.01, 1000))

            u.add_to_time_spent(result.discoveryLatency)
            iot_device_time_consumed += result.discoveryLatency
            # charge_c is in [C], so we should divide by dc to get the current
            current_c = result.chargeAdv / result.discoveryLatency
            u.add_to_power_consumed(current_c)
            iot_device_power_consumed += current_c

            # at the end of discovery the device go through connection establishment
            # as per documentation there is no duration, since it is accounted in the discovery
            # For user we set periodic scan type and to be the master
            duration = \
                (self.network.network_impl.connection_establishment.ble_e_model_ce_get_duration_for_connection_procedure
                 (1, 0, 1,
                  0,
                  0.1))
            u.add_to_time_spent(duration)

            u.add_to_power_consumed(
                self.network.network_impl.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
                (1, 0, 1,
                 0,
                 0.1) / duration)

            duration = \
                (self.network.network_impl.connection_establishment.ble_e_model_ce_get_duration_for_connection_procedure
                 (1, 0, 0,
                  0,
                  0.1))
            iot_device_time_consumed += duration
            iot_device_power_consumed += (
                self.network.network_impl.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
                (1, 0, 0,
                 0,
                 0.1) / duration)

            # the owner (slave) sends PP to the user (master)
            duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(0, 0.1, 1,
                                                                                                [owner_pp_size],
                                                                                                [owner_pp_size], 3)

            iot_device_time_consumed += duration

            iot_device_power_consumed += self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(0, 0.1,
                                                                                                                1,
                                                                                                                [
                                                                                                                    owner_pp_size],
                                                                                                                [
                                                                                                                    owner_pp_size],
                                                                                                                3) / duration

            # user sends the consent to the owner
            duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                [owner_pp_size],
                                                                                                [owner_pp_size], 3)

            u.add_to_time_spent(duration)

            u.add_to_power_consumed(self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                           [
                                                                                                               owner_pp_size],
                                                                                                           [
                                                                                                               owner_pp_size],
                                                                                                           3) / duration)

        voltage = 3.3  # We assume that BLE devices operate at 3.3V
        # convert from As to Ws
        u.power_consumed = u.power_consumed * voltage
        iot_device.add_to_power_consumed(iot_device_power_consumed * voltage)
        iot_device.add_to_time_spent(iot_device_time_consumed)

    def zigbee_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        ZigBee-based Concession negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT device.
        :return: Power and time consumption of user and iot device.
        """

        # has to be local not to double count
        iot_device_power_consumed = 0
        iot_device_time_consumed = 0

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u.consent:
            # get the duration and power consumption of startup for the device (Ws, s)
            charge_c, dc = self.network.network_impl.startup()

            u.add_to_time_spent(dc)
            iot_device_time_consumed += dc
            u.add_to_power_consumed(charge_c)
            iot_device_power_consumed += charge_c

            # Association duration and power consumption (Ws, s)

            charge_a, da = self.network.network_impl.association()

            u.add_to_time_spent(da)
            iot_device_time_consumed += da
            u.add_to_power_consumed(charge_a)
            iot_device_power_consumed += charge_a

            # at the end of association the Coordinator sends its PP to the mote

            charge_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            charge_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            u.add_to_time_spent(d_rx)
            iot_device_time_consumed += d_tx
            u.add_to_power_consumed(charge_rx)
            iot_device_power_consumed += charge_tx

            # Send ACK
            charge_tx, d_tx = self.network.network_impl.send(self.network.network_impl.ack_size)
            charge_rx, d_rx = self.network.network_impl.receive(self.network.network_impl.ack_size)

            u.add_to_time_spent(d_tx)
            iot_device_time_consumed += d_rx
            u.add_to_power_consumed(charge_tx)
            iot_device_power_consumed += charge_rx

            # the mote sends its consent to the Coordinator

            charge_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            charge_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            u.add_to_time_spent(d_tx)
            iot_device_time_consumed += d_rx
            u.add_to_power_consumed(charge_tx)
            iot_device_power_consumed += charge_rx

            # Send ACK
            charge_tx, d_tx = self.network.network_impl.send(self.network.network_impl.ack_size)
            charge_rx, d_rx = self.network.network_impl.receive(self.network.network_impl.ack_size)

            u.add_to_time_spent(d_tx)
            iot_device_time_consumed += d_rx
            u.add_to_power_consumed(charge_tx)
            iot_device_power_consumed += charge_rx

        iot_device.add_to_time_spent(iot_device_time_consumed)
        iot_device.add_to_power_consumed(iot_device_power_consumed)

    def lora_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        LoRa-based Concession negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT device.
        :return: Power and time consumption of user and iot device.
        """

        # has to be local not to double count
        iot_device_power_consumed = 0
        iot_device_time_consumed = 0

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u.consent:
            # IoT device (owner) sends PP to the LoRa node (user)

            power_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            u.add_to_time_spent(d_rx)
            iot_device_time_consumed += d_tx
            u.add_to_power_consumed(power_rx)
            iot_device_power_consumed += power_tx

            # the LoRa node replies with consent (same PP)
            power_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            u.add_to_time_spent(d_tx)
            iot_device_time_consumed += d_rx
            u.add_to_power_consumed(power_tx)
            iot_device_power_consumed += power_rx

        iot_device.add_to_power_consumed(iot_device_power_consumed)
        iot_device.add_to_time_spent(iot_device_time_consumed)
