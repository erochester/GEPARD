from concurrent.futures import ThreadPoolExecutor

from util import check_distance, calc_utility, calc_time_remaining
import random
import sys
import logging
from functools import reduce
import numpy as np


class Alanezi:
    """
    Implements Alanezi negotiation protocol. Includes BLE, ZigBee and LoRa based negotiations.
    """

    def __init__(self, network):
        """
        Initializes Alanezi class.
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

        # As per the original work, we assume 217 and 639 bytes the sizes of PP
        # Can be changed to dynamic sizing (create real PPs and collect their size)
        user_pp_size = 217
        owner_pp_size = 639

        # For now, we assume that the IoT owner precisely knows the user's privacy preferences and
        #  what to offer to them. We can add the estimator further down the line
        #  for now we go through the list of users, offer to them the privacy policies and
        #  see if they consent and if it is after 1 phase or 2 phases

        # first we define the values for privacy dimensions for different policies. (t, r, s, i) as per Alanezi
        privacy_dim = [(3, 3, 1, 3), (5, 1, 1, 1), (2, 2, 2, 2), (2, 1, 2, 2)]
        # these are used in calculating utility when offering PP to a user
        # we define these as an example values.
        # For example, privacy_dim[2] can be imagined as:
        # Data Type(t): Detailed user behavior data(e.g., clickstreams, purchase history)
        # Retention(r): 2 years
        # Sharing(s): Shared with 2 third parties
        # Inference(i): Extensive inference(e.g., behavioral profiling, predictive analytics)

        # remove users that are > x m away from IoT device (outside the communication range, but not sensing)
        # For example, 50 meters for BLE

        applicable_users = []
        for u in curr_users_list:
            if check_distance(u.curr_loc, self.network.network_impl.comm_distance):
                applicable_users.append(u)

        applicable_users = [u for u in applicable_users if not u.neg_attempted]

        logging.debug("Applicable users: %s", [u.id_ for u in applicable_users])

        # if no applicable users left we return
        if applicable_users:
            temp_list = []
            for u in applicable_users:
                # check if user already consented and if not
                if not u.consent:
                    # we tried negotiating with the user
                    u.update_neg_attempted()
                    # check the user's privacy label
                    if u.privacy_label == 1:
                        # for fundamentalists, we offer PP4
                        priv_policy = privacy_dim[3]
                        # as per work gamma is a value in range (0.843,1]
                        gamma = random.uniform(0.843, 1.0)
                        # combination of these values makes sure that only 20.4% of fundamentalists consent
                        util = (-gamma * reduce((lambda x, y: x * y), list(priv_policy))) + sum(list(priv_policy))
                        logging.debug("User %d privacy label %d (fundamentalist) and utility %f", u.id_, u.privacy_label, util)
                        if util >= 0:
                            logging.debug("will consent in 1 round")
                            u.update_consent(1)
                            # TODO: add to other neg. algos
                            temp_list.append(u)
                    elif u.privacy_label == 2:
                        # for pragmatists, we have potentially 2-phase negotiation
                        # we first offer PP3
                        # priv_policy = privacy_dim[2]
                        # as per work gamma is a value in range (0.25, 75]
                        gamma = random.uniform(0.26, 0.75)
                        logging.debug("User %d privacy label %d (pragmatist) and gamma %d", u.id_, u.privacy_label, gamma)
                        # if gamma is too large we will not consent
                        # otherwise at least 1 round
                        if gamma > 0.368:
                            # single phase consent
                            logging.debug("will consent in 1 round")
                            u.update_consent(1)
                            temp_list.append(u)
                        else:
                            # two phase consent
                            logging.debug("will consent in 2 rounds")
                            u.update_consent(2)
                            temp_list.append(u)
                    else:
                        logging.debug("User %d privacy label %d (unconcerned)", u.id_, u.privacy_label)
                        logging.debug("will consent in 1 round")
                        # for unconcerned we always consent with 1 phase
                        u.update_consent(1)
                        temp_list.append(u)
                else:
                    # if user already consented we don't do anything
                    # shouldn't occur, since we remove all consented users beforehand
                    logging.error("Something went wrong in Alanezi. There is a user that has already consented.")
                    exit(-1)

            applicable_users = temp_list

            logging.debug("Applicable users that will consent: %s", [u.id_ for u in applicable_users])

            if applicable_users:
                # Create a list of dictionaries containing arguments for the function
                user_data_list = [{"user_data": user_data, "user_pp_size": user_pp_size, "owner_pp_size": owner_pp_size,
                                   "applicable_users": applicable_users,
                                   "iot_device": iot_device}
                                  for user_data in enumerate(applicable_users)]

                # Use multithreading to parallelize the for loop
                # Couldn't use the ProcessPoolExecutor as it clones the objects and does not return the results
                # Can still be easily replaced if necessary
                # Reference:
                # https://stackoverflow.com/questions/41164606/altering-different-python-objects-in-parallel-processes-respectively
                with ThreadPoolExecutor() as executor:
                    # Map the function over the user data list
                    list(executor.map(self.consumption_for_user, user_data_list))
                    executor.shutdown(wait=True, cancel_futures=False)

    # Define a function to calculate power consumption and duration with a single user
    def consumption_for_user(self, args):
        """
        Used to parallelize the consumption calculations since BLE library takes a while to compute.
        :param args: Arguments used to run the functions. Includes: user_data, user_pp_size, owner_pp_size,
        user_consent_obj, user_consent, applicable_users, iot_device.
        :return: Returns total device power and time consumption, as well as the updated user lists.
        """

        index, u = args["user_data"]
        user_pp_size = args["user_pp_size"]
        owner_pp_size = args["owner_pp_size"]
        iot_device = args["iot_device"]

        if u.consent == 0:
            logging.error("Something went wrong in Alanezi. There is a user that has not consented but we try to process them.")
            exit(-1)

        # check if the current user is going to negotiate:
        if u.consent > 0:
            if self.network.network_type == "ble":
                # Calculate the power consumption and duration for BLE
                self.ble_negotiation(user_pp_size, owner_pp_size, u, iot_device)
            elif self.network.network_type == "zigbee":
                # Calculate the power consumption and duration for Zigbee
                self.zigbee_negotiation(user_pp_size, owner_pp_size, u, iot_device)
            elif self.network.network_type == "lora":
                # Calculate the power consumption and duration for LoRa
                self.lora_negotiation(user_pp_size, owner_pp_size, u, iot_device)
            else:
                # raise error and exit
                logging.error("Invalid network type in alanezi.py.")
                sys.exit(1)

            # Calculate user and owner utility
            u.add_to_utility(calc_utility(calc_time_remaining(u), u.power_consumed,
                                          u.weights))
            # Use the user remaining time to calculate the IoT device utility,
            # since the user is moving away (not the device)
            iot_device.add_to_utility(calc_utility(calc_time_remaining(u),
                                                   iot_device.power_consumed, iot_device.weights))
            if iot_device.utility == float("inf"):
                # raise error and exit
                logging.error("Got infinite utility for IoT device in alanezi.py.")
                sys.exit(-1)

    def ble_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        BLE-based Alanezi negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT device object.
        :return: Power and time consumption of user and iot device.
        """

        # Alanezi's proposed negotiation follows the following flow:
        # BLE broadcast with data request information (user is advertising and IoT owner is scanning, user PP is sent)
        # -> connection establishment -> IoT owner accepts/negotiation -> …done?

        # Consequently, no matter the number of phases the advertising, scanning and connection establishment with
        # at least 1 connection packet always occurs
        # We use the values directly provided by Kindt et al.

        # has to be local not to double count
        iot_device_power_consumed = 0
        iot_device_time_consumed = 0

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
        # the discovery includes PP exchange as the first round
        result = (self.network.network_impl.discovery.ble_model_discovery_get_result_alanezi
                  (100, 0.9999, 0.25, 5, 2, 0.01, 1000, user_pp_size))

        u.add_to_time_spent(result.discoveryLatency)
        iot_device_time_consumed += result.discoveryLatency
        # charge_c is in [C], so we should divide by dc to get the current
        current_c = result.chargeAdv / result.discoveryLatency
        u.add_to_power_consumed(current_c)
        iot_device_power_consumed += current_c

        # at the end of discovery the device go through connection establishment
        # as per documentation there is no duration, since it is accounted in the discovery
        # For user we set periodic scan type

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

        # if owner accepts in 1-phase then owner starts sending/collecting the data, and we are done
        # exchanged during device discovery phase
        # if negotiation is 2 phases
        if u == 2:
            # in 2 phase negotiation we start exactly the same way as in 1 phase
            # however now the owner responds with an alternative proposal and waits for the user to reply
            # so two more steps are added

            # Note that we assume that there is no delay between connection establishment and sending first packet
            # after connection establishment the owner sends the proposal and the user receives it
            # We assume that the user reply is the received PP
            # we call from master point of view because it has Tx first and then Rx which better simulates the behaviour
            duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                  [owner_pp_size],
                                                                                                  [owner_pp_size], 3)
            u.add_to_time_spent(duration)
            iot_device_time_consumed += duration

            power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                 [owner_pp_size],
                                                                                                 [owner_pp_size], 3)
            u.add_to_power_consumed(power_spent / duration)
            iot_device_power_consumed += (power_spent / duration)

        voltage = 3.3  # We assume that BLE devices operate at 3.3V
        # convert from As to Ws
        u.power_consumed = u.power_consumed * voltage
        iot_device.add_to_power_consumed(iot_device_power_consumed * voltage)
        iot_device.add_to_time_spent(iot_device_time_consumed)

    def zigbee_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        ZigBee-based Alanezi negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT device object.
        :return: Power and time consumption of user and iot device.
        """

        # Alanezi's proposed negotiation follows the following flow:
        # broadcast with data request information (user is advertising and IoT owner is scanning, user PP is sent)
        # -> connection establishment -> IoT owner accepts/negotiation -> …done?

        # We adjust the negotiation flow to fit Zigbee as follows:
        # ZigBee Mote (user) starts up ->
        # -> Mote associates with the Coordinator (IoT device) -> Mote sends data request information to Coordinator
        # -> Coordinator accepts/negotiation -> ...done?

        # has to be local not to double count
        iot_device_power_consumed = 0
        iot_device_time_consumed = 0

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

        # at the end of association the mote sends its request to the coordinator
        charge_tx, d_tx = self.network.network_impl.send(user_pp_size)
        charge_rx, d_rx = self.network.network_impl.receive(user_pp_size)

        u.add_to_time_spent(d_tx)
        iot_device_time_consumed += d_rx
        u.add_to_power_consumed(charge_tx)
        iot_device_power_consumed += charge_rx

        # the owner also needs to send an ACK to the mote
        # as per: https://github.com/Koenkk/zigbee2mqtt/issues/1455
        # ACK size is 65 bytes

        charge_tx, d_tx = self.network.network_impl.send(self.network.network_impl.ack_size)
        charge_rx, d_rx = self.network.network_impl.receive(self.network.network_impl.ack_size)

        u.add_to_time_spent(d_rx)
        iot_device_time_consumed += d_tx
        u.add_to_power_consumed(charge_rx)
        iot_device_power_consumed += charge_tx

        # if owner accepts in 1-phase then owner starts sending/collecting the data, and we are done
        # the PP exchange occurred during device discovery

        # if negotiation is 2 phases
        if u == 2:
            # in 2 phase negotiation we start exactly the same way as in 1 phase
            # however now the owner responds with an alternative proposal and waits for the user to reply
            # so two more steps are added

            # Note that we assume that there is no delay between association and sending first packet
            # after connection establishment the owner sends the proposal and the user receives it
            # We assume that the user reply is the received PP
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

        iot_device.add_to_time_spent(iot_device_time_consumed)
        iot_device.add_to_power_consumed(iot_device_power_consumed)

    def lora_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        LoRa-based Alanezi negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT device object.
        :return: Power and time consumption of user and iot device.
        """

        # Alanezi's proposed negotiation follows the following flow:
        # broadcast with data request information (user is advertising and IoT owner is scanning, user PP is sent)
        # -> connection establishment -> IoT owner accepts/negotiation -> …done?

        # We adjust the negotiation flow to fit Lora as follows:
        # Class A LoRa node sends data request information to the Gateway
        # -> Gateway accepts/negotiation -> ...done?

        # has to be local not to double count
        iot_device_power_consumed = 0
        iot_device_time_consumed = 0

        # LoRa device (user) sends its request to the Gateway (owner)
        power_tx, d_tx = self.network.network_impl.send(user_pp_size)

        # Gateway reception
        power_rx, d_rx = self.network.network_impl.receive(user_pp_size)

        u.add_to_time_spent(d_tx)
        iot_device_time_consumed += d_rx
        u.add_to_power_consumed(power_tx)
        iot_device_power_consumed += power_rx

        # if owner accepts in 1-phase then owner starts sending/collecting the data and we are done

        # if negotiation is 2 phases
        if u == 2:
            # in 2 phase negotiation we start exactly the same way as in 1 phase
            # however now the owner responds with an alternative proposal and waits for the user to reply
            # so two more steps are added

            # Gateway (owner) sends alternative offer
            power_tx, d_tx = self.network.network_impl.send(owner_pp_size)

            # LoRa node reception
            power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            u.add_to_time_spent(d_tx)
            iot_device_time_consumed += d_rx
            u.add_to_power_consumed(power_tx)
            iot_device_power_consumed += power_rx

            # Acceptance
            # LoRa device (user) sends back the same PP it received
            power_tx, d_tx = self.network.network_impl.send(owner_pp_size)

            # Gateway reception
            power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            u.add_to_time_spent(d_tx)
            iot_device_time_consumed += d_rx
            u.add_to_power_consumed(power_tx)
            iot_device_power_consumed += power_rx

        iot_device.add_to_power_consumed(iot_device_power_consumed)
        iot_device.add_to_time_spent(iot_device_time_consumed)
