from util import check_distance, calc_utility, calc_time_remaining
import random
import numpy as np
import sys


class Concession:

    def __init__(self, network):
        self.network = network
        self.user_utility = {}

    def run(self, curr_users_list, iot_device):
        # list of consented users
        user_consent = []

        user_pp_size = 38
        owner_pp_size = 86

        total_user_power_consumption = 0
        total_owner_power_consumption = 0

        total_user_time_spent = 0
        total_owner_time_spent = 0

        # Create dictionary of user's utility where user's id is the key
        self.user_utility = {}

        # remove users that are > x meters away from IoT device
        applicable_users = []
        distance = self.network.network_impl.comm_distance
        for u in curr_users_list:
            if check_distance(u.curr_loc, distance) and not u.consent:
                applicable_users.append(u)

        for round in range(5):
            # If all users have already consented, exit negotiation
            if len(applicable_users) == len(user_consent):
                break

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
                    highest_utility_user.update_consent(True)
                    user_consent.append(highest_utility_user)
            # everyone else consents
            else:
                highest_utility_user.update_consent(True)
                user_consent.append(highest_utility_user)

            if highest_utility_user.consent:

                if self.network.network_type == "ble":
                    # Calculate the power consumption and duration for BLE
                    (curr_user_power_consumption, curr_owner_power_consumption, curr_user_time_spent,
                     curr_owner_time_spent) = self.ble_negotiation(user_pp_size, owner_pp_size, highest_utility_user)
                elif self.network.network_type == "zigbee":
                    # Calculate the power consumption and duration for zigbee
                    (curr_user_power_consumption, curr_owner_power_consumption, curr_user_time_spent,
                     curr_owner_time_spent) = self.zigbee_negotiation(user_pp_size, owner_pp_size, highest_utility_user)
                elif self.network.network_type == "lora":
                    # Calculate the power consumption and duration for zigbee
                    (curr_user_power_consumption, curr_owner_power_consumption, curr_user_time_spent,
                     curr_owner_time_spent) = self.lora_negotiation(user_pp_size, owner_pp_size, highest_utility_user)
                else:
                    # raise error and exit
                    print("Invalid network type in concession.py.")
                    sys.exit(1)

                total_owner_power_consumption += curr_owner_power_consumption
                total_owner_time_spent += curr_owner_time_spent
                total_user_power_consumption += curr_user_power_consumption
                total_user_time_spent += curr_user_time_spent

                # update utility
                user_utility = calc_utility(calc_time_remaining(highest_utility_user), total_user_power_consumption,
                                            highest_utility_user.weights)
                highest_utility_user.update_utility(highest_utility_user.utility + user_utility)

                owner_utility = calc_utility(calc_time_remaining(highest_utility_user),
                                             total_owner_power_consumption, iot_device.weights)
                iot_device.update_utility(iot_device.utility + owner_utility)

        return user_consent, applicable_users, total_user_power_consumption, total_owner_power_consumption, \
            total_user_time_spent, total_owner_time_spent

    def calc_assumed_utility(self, user):
        # Calculate user's utility given how much longer the user stays in the environment

        # Get user id
        user_id = user.id_

        # Calculate time it takes for user to reach destination
        time = calc_time_remaining(user)

        # Calculate user's utility using exponential decay function
        utility = np.exp(-time)

        # Add user's utility to dictionary
        self.user_utility[user_id] = utility

    def ble_negotiation(self, user_pp_size, owner_pp_size, u):
        total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent \
            = 0, 0, 0, 0

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u.consent:
            # get the duration of all constant parts of a connection event. (Preprocessing, Postprocessing,...)
            dc = self.network.network_impl.connected.ble_e_model_c_get_duration_constant_parts()

            # now do the same with the charge of these phases
            charge_c = self.network.network_impl.connected.ble_e_model_c_get_charge_constant_parts()

            total_user_time_spent += dc
            total_owner_time_spent += dc
            total_user_power_consumption += charge_c
            total_owner_power_consumption += charge_c

            # Calculate the latency and energy consumption of device discovery. The values are taken from:
            # https://www.researchgate.net/publication/335808941_Connection-less_BLE_Performance_Evaluation_on_Smartphones
            result = (self.network.network_impl.discovery.ble_model_discovery_get_result
                      (100, 0.9999, 0.25, 5, 2, 0.01, 1000))

            total_user_time_spent += result.discoveryLatency
            total_owner_time_spent += result.discoveryLatency
            total_user_power_consumption += result.chargeAdv
            total_owner_power_consumption += result.chargeScan

            # at the end of discovery the device go through connection establishment
            # as per documentation there is no duration, since it is accounted in the discovery
            # For user we set periodic scan type and to be the master
            total_user_power_consumption += (
                self.network.network_impl.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
                (1, 0, 1,
                 0,
                 0.1))
            # owner is the slave
            total_owner_power_consumption += (
                self.network.network_impl.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
                (1, 0, 0,
                 0,
                 0.1))

            # the owner (slave) sends PP to the user (master)
            time_spent = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(0, 0.1, 1,
                                                                                                  [user_pp_size],
                                                                                                  [owner_pp_size], 3)

            total_owner_time_spent += time_spent

            # user sends the consent to the owner
            time_spent = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                  [owner_pp_size],
                                                                                                  [user_pp_size], 3)

            total_user_time_spent += time_spent

            power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(0, 0.1, 1,
                                                                                                 [user_pp_size],
                                                                                                 [owner_pp_size], 3)
            total_owner_power_consumption += power_spent

            power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                 [owner_pp_size],
                                                                                                 [user_pp_size], 3)
            total_user_power_consumption += power_spent

        return total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent

    def zigbee_negotiation(self, user_pp_size, owner_pp_size, u):
        total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent \
            = 0, 0, 0, 0

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u.consent:
            # get the duration and power consumption of startup for the device (Ws, s)
            charge_c, dc = self.network.network_impl.startup()

            total_user_time_spent += dc
            total_owner_time_spent += dc
            total_user_power_consumption += charge_c
            total_owner_power_consumption += charge_c

            # Association duration and power consumption (Ws, s)

            charge_a, da = self.network.network_impl.association()

            total_user_time_spent += da
            total_owner_time_spent += da
            total_user_power_consumption += charge_a
            total_owner_power_consumption += charge_a

            # at the end of association the Coordinator sends its PP to the mote

            charge_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            charge_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            total_user_time_spent += d_rx
            total_owner_time_spent += d_tx
            total_user_power_consumption += charge_rx
            total_owner_power_consumption += charge_tx

            # the mote sends its consent to the Coordinator

            charge_tx, d_tx = self.network.network_impl.send(user_pp_size)
            charge_rx, d_rx = self.network.network_impl.receive(user_pp_size)

            total_user_time_spent += d_tx
            total_owner_time_spent += d_rx
            total_user_power_consumption += charge_tx
            total_owner_power_consumption += charge_rx

        return total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent

    def lora_negotiation(self, user_pp_size, owner_pp_size, u):
        total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent \
            = 0, 0, 0, 0

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u.consent:
            # IoT device (owner) sends PP to the LoRa node (user)

            power_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            total_user_time_spent += d_rx
            total_owner_time_spent += d_tx
            total_user_power_consumption += power_rx
            total_owner_power_consumption += power_tx

            # the LoRa node replies with consent (user PP)
            power_tx, d_tx = self.network.network_impl.send(user_pp_size)
            power_rx, d_rx = self.network.network_impl.receive(user_pp_size)

            total_user_time_spent += d_tx
            total_owner_time_spent += d_rx
            total_user_power_consumption += power_tx
            total_owner_power_consumption += power_rx

        return total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent
