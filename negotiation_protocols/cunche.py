from concurrent.futures import ProcessPoolExecutor

from util import check_distance, calc_utility, calc_time_remaining
import random
import sys


class Cunche:
    """
    Implements Cunche negotiation algorithm. Includes BLE, ZigBee and LoRa based negotiations.
    """

    def __init__(self, network):
        """
        Initializes Cunche class.
        :param network: network type (e.g., BLE)
        """
        self.network = network

    def run(self, curr_users_list, iot_device):
        """
        Main driver for the negotiations. Sets up the main parameter, determines applicable user set for the
        negotiations, calls multiprocessor to run the negotiation matching the network type selected and processes
        the results.
        :param curr_users_list: list of current users in the environment (Users object).
        :param iot_device: IoT device object.
        :return: Returns total device power and time consumption, as well as the updated user lists.
        """

        # Privacy policy size in bytes
        user_pp_size = 38
        owner_pp_size = 86

        # remove users that are > x meters away from IoT device
        applicable_users = []
        distance = self.network.network_impl.comm_distance
        for u in curr_users_list:
            if check_distance(u.curr_loc, distance):
                applicable_users.append(u)

        # list of consented users
        user_consent = []
        user_consent_obj = []

        for u in applicable_users:
            # check if user already consented and if not
            if not u.consent:
                # check the user's privacy label
                if u.privacy_label == 1:
                    # for fundamentalists, we offer we see if user is in 79.6% non-consenting
                    if random.random() > 0.796:
                        # of these only 25% consent in first phase and 75% in second phase
                        if random.random() <= 0.25:
                            u.update_consent(True)
                            user_consent_obj.append(u)
                            user_consent.append(1)
                        else:
                            u.update_consent(True)
                            user_consent_obj.append(u)
                            user_consent.append(2)
                    else:
                        # the rest do not consent
                        user_consent_obj.append(u)
                        user_consent.append(0)
                elif u.privacy_label == 2:
                    # for privacy pragmatists 26.45% do not consent
                    # of the remaining 73.55%, 75% consent in first phase and 25% in second phase
                    if random.random() >= 0.7355:
                        if random.random() <= 0.75:
                            u.update_consent(True)
                            user_consent_obj.append(u)
                            user_consent.append(1)
                        else:
                            u.update_consent(True)
                            user_consent_obj.append(u)
                            user_consent.append(2)
                # everyone else consents in 1 phase
                else:
                    u.update_consent(True)
                    user_consent_obj.append(u)
                    user_consent.append(1)

        # Initialize total variables outside the loop
        total_user_current_consumption = 0
        total_user_time_spent = 0
        total_owner_current_consumption = 0
        total_owner_time_spent = 0

        # Create a list of dictionaries containing arguments for the function
        user_data_list = [{"user_data": user_data, "user_pp_size": user_pp_size, "owner_pp_size": owner_pp_size,
                           "user_consent_obj": user_consent_obj, "user_consent": user_consent,
                           "applicable_users": applicable_users,
                           "iot_device": iot_device}
                          for user_data in enumerate(user_consent)]

        # Use multiprocessing to parallelize the for loop
        with ProcessPoolExecutor() as executor:
            # Map the function over the user data list
            results = list(executor.map(self.consumption_for_user, user_data_list))
            executor.shutdown(wait=True, cancel_futures=False)

        index = 0

        # Sum up the results after the processes are done
        for result in results:
            total_user_current_consumption += result[0]
            total_user_time_spent += result[1]
            total_owner_current_consumption += result[2]
            total_owner_time_spent += result[3]

            # Update utility
            applicable_users[index].update_utility(result[4])
            iot_device.update_utility(iot_device.utility + result[5])
            index += 1

        # now we can return the number of contacted users, how many consented, after how much time and
        # how much energy was consumed
        return user_consent_obj, applicable_users, total_user_current_consumption, total_owner_current_consumption, \
            total_user_time_spent, total_owner_time_spent

    # Define a function to calculate power consumption and duration with a single user
    def consumption_for_user(self, args):
        """
        Used to parallelize the consumption calculations since BLE library takes a while to compute.
        :param args: Arguments used to run the functions. Includes: user_data, user_pp_size, owner_pp_size,
        user_consent_obj, user_consent, applicable_users, iot_device.
        :return: Returns total device power and time consumption, as well as the updated user lists.
        """

        (curr_user_power_consumption, curr_user_time_spent, curr_owner_power_consumption, curr_owner_time_spent,
         user_utility, owner_utility) = 0, 0, 0, 0, 0, 0

        index, u = args["user_data"]
        user_pp_size = args["user_pp_size"]
        owner_pp_size = args["owner_pp_size"]
        user_consent_obj = args["user_consent_obj"]
        user_consent = args["user_consent"]
        applicable_users = args["applicable_users"]
        iot_device = args["iot_device"]

        # shouldn't occur, since we remove all consented users beforehand
        if not user_consent_obj[index].consent:
            return 0, 0, 0, 0, 0, 0

        if self.network.network_type == "ble":
            # Calculate the power consumption and duration for BLE
            (curr_user_power_consumption, curr_owner_power_consumption, curr_user_time_spent,
             curr_owner_time_spent) = self.ble_negotiation(user_pp_size, owner_pp_size, u)
        elif self.network.network_type == "zigbee":
            # Calculate the power consumption and duration for zigbee
            (curr_user_power_consumption, curr_owner_power_consumption, curr_user_time_spent,
             curr_owner_time_spent) = self.zigbee_negotiation(user_pp_size, owner_pp_size, u)
        elif self.network.network_type == "lora":
            # Calculate the power consumption and duration for zigbee
            (curr_user_power_consumption, curr_owner_power_consumption, curr_user_time_spent,
             curr_owner_time_spent) = self.lora_negotiation(user_pp_size, owner_pp_size, u)
        else:
            # raise error and exit
            print("Invalid network type in concession.py.")
            sys.exit(1)

        # Calculate user and owner utility
        # update utility
        user_utility = calc_utility(calc_time_remaining(user_consent_obj[index]), curr_user_power_consumption,
                                    user_consent_obj[index].weights)
        user_consent_obj[index].update_utility(user_consent_obj[index].utility + user_utility)

        owner_utility = calc_utility(calc_time_remaining(user_consent_obj[index]), curr_owner_power_consumption,
                                     iot_device.weights)
        iot_device.update_utility(iot_device.utility + owner_utility)

        # Return the local results
        return curr_user_power_consumption, curr_user_time_spent, curr_owner_power_consumption, curr_owner_time_spent, user_utility, owner_utility

    def ble_negotiation(self, user_pp_size, owner_pp_size, u):
        """
        BLE-based Cunche negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :return: Power and time consumption of user and iot device.
        """
        total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent \
            = 0, 0, 0, 0

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u > 0:
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

            if u == 1:
                # user sends the consent to the owner
                time_spent = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                      [0],
                                                                                                      [user_pp_size], 3)

                total_user_time_spent += time_spent

                power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(0, 0.1, 1,
                                                                                                     [user_pp_size],
                                                                                                     [0], 3)
                total_owner_power_consumption += power_spent

                power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                     [user_pp_size],
                                                                                                     [user_pp_size], 3)
                total_user_power_consumption += power_spent

            elif u == 2:
                # user forwards PP to the iot
                # the owner then forwards "modified" PP to the user
                # TODO: this is not implemented yet, so we just assume it is the same as the PP sent to the user
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

            else:
                print("Invalid consent value in cunche.py.")
                sys.exit(1)

        return total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent

    def zigbee_negotiation(self, user_pp_size, owner_pp_size, u):
        """
        ZigBee-based Cunche negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :return: Power and time consumption of user and iot device.
        """
        total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent \
            = 0, 0, 0, 0

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u > 0:
            # get the duration and power consumption of startup for the device (W, s)
            charge_c, dc = self.network.network_impl.startup()

            total_user_time_spent += dc
            total_owner_time_spent += dc
            total_user_power_consumption += charge_c
            total_owner_power_consumption += charge_c

            # Association duration and power consumption (W, s)

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

            if u == 1:
                # the mote sends its consent to the Coordinator

                charge_tx, d_tx = self.network.network_impl.send(user_pp_size)
                charge_rx, d_rx = self.network.network_impl.receive(user_pp_size)

                total_user_time_spent += d_tx
                total_owner_time_spent += d_rx
                total_user_power_consumption += charge_tx
                total_owner_power_consumption += charge_rx
            elif u == 2:
                # the mote sends its PP to the Coordinator

                charge_tx, d_tx = self.network.network_impl.send(user_pp_size)
                charge_rx, d_rx = self.network.network_impl.receive(user_pp_size)

                total_user_time_spent += d_tx
                total_owner_time_spent += d_rx
                total_user_power_consumption += charge_tx
                total_owner_power_consumption += charge_rx

                # the Coordinator sends the modified PP to the mote
                charge_tx, d_tx = self.network.network_impl.send(owner_pp_size)
                charge_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

                total_user_time_spent += d_rx
                total_owner_time_spent += d_tx
                total_user_power_consumption += charge_rx
                total_owner_power_consumption += charge_tx
            else:
                print("Invalid consent value in cunche.py.")
                sys.exit(1)

        return total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent

    def lora_negotiation(self, user_pp_size, owner_pp_size, u):
        """
        LoRa-based Cunche negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :return: Power and time consumption of user and iot device.
        """
        total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent \
            = 0, 0, 0, 0

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u > 0:
            # IoT device (owner) sends PP to the LoRa node (user)

            power_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            total_user_time_spent += d_rx
            total_owner_time_spent += d_tx
            total_user_power_consumption += power_rx
            total_owner_power_consumption += power_tx

            if u == 1:
                # the LoRa node replies with consent (user PP)
                power_tx, d_tx = self.network.network_impl.send(user_pp_size)
                power_rx, d_rx = self.network.network_impl.receive(user_pp_size)

                total_user_time_spent += d_tx
                total_owner_time_spent += d_rx
                total_user_power_consumption += power_tx
                total_owner_power_consumption += power_rx
            elif u == 2:
                # the LoRa node replies with its PP
                power_tx, d_tx = self.network.network_impl.send(user_pp_size)
                power_rx, d_rx = self.network.network_impl.receive(user_pp_size)

                total_user_time_spent += d_tx
                total_owner_time_spent += d_rx
                total_user_power_consumption += power_tx
                total_owner_power_consumption += power_rx

                # the IoT device replies with modified PP
                power_tx, d_tx = self.network.network_impl.send(owner_pp_size)
                power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

                total_user_time_spent += d_rx
                total_owner_time_spent += d_tx
                total_user_power_consumption += power_rx
                total_owner_power_consumption += power_tx
            else:
                print("Invalid consent value in cunche.py.")
                sys.exit(1)

        return (total_user_power_consumption, total_owner_power_consumption, total_user_time_spent,
                total_owner_time_spent)
