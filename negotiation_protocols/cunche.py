from concurrent.futures import ThreadPoolExecutor

from util import check_distance, calc_utility, calc_time_remaining
import random
import sys
import logging


class Cunche:
    """
    Implements Cunche negotiation protocol. Includes BLE, ZigBee and LoRa based negotiations.
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

        for u in applicable_users:
            # check if user already consented and if not
            if not u.consent:
                # check the user's privacy label
                if u.privacy_label == 1:
                    # for fundamentalists, we offer we see if user is in 79.6% non-consenting
                    if random.random() > 0.796:
                        # of these only 25% consent in first phase and 75% in second phase
                        if random.random() <= 0.25:
                            u.update_consent(1)
                        else:
                            u.update_consent(2)
                    else:
                        # the rest do not consent
                        u.update_consent(0)
                elif u.privacy_label == 2:
                    # for privacy pragmatists 26.45% do not consent
                    # of the remaining 73.55%, 75% consent in first phase and 25% in second phase
                    if random.random() >= 0.7355:
                        if random.random() <= 0.75:
                            u.update_consent(1)
                        else:
                            u.update_consent(2)
                # everyone else consents in 1 phase
                else:
                    u.update_consent(1)

        # Create a list of dictionaries containing arguments for the function
        user_data_list = [{"user_data": user_data, "user_pp_size": user_pp_size, "owner_pp_size": owner_pp_size,
                           "applicable_users": applicable_users,
                           "iot_device": iot_device}
                          for user_data in enumerate(applicable_users)]

        # Use multiprocessing to parallelize the for loop
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

        # check if the current user is going to negotiate:
        if u.consent > 0:
            if self.network.network_type == "ble":
                # Calculate the power consumption and duration for BLE
                self.ble_negotiation(user_pp_size, owner_pp_size, u, iot_device)
            elif self.network.network_type == "zigbee":
                # Calculate the power consumption and duration for zigbee
                self.zigbee_negotiation(user_pp_size, owner_pp_size, u, iot_device)
            elif self.network.network_type == "lora":
                # Calculate the power consumption and duration for zigbee
                self.lora_negotiation(user_pp_size, owner_pp_size, u, iot_device)
            else:
                # raise error and exit
                logging.error("Invalid network type in cunche.py.")
                sys.exit(-1)

            # Calculate user and owner utility
            u.add_to_utility(calc_utility(calc_time_remaining(u), u.power_consumed,
                                          u.weights))
            # Use the user remaining time to calculate the IoT device utility,
            # since the user is moving away (not the device)
            iot_device.add_to_utility(calc_utility(calc_time_remaining(u),
                                                   iot_device.power_consumed, iot_device.weights))
            if iot_device.utility == float("inf"):
                # raise error and exit
                logging.error("Got infinite utility for IoT device in cunche.py.")
                sys.exit(-1)

    def ble_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        BLE-based Cunche negotiation implementation.
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
        if u.consent > 0:
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
            current_c = result.chargeScan / result.discoveryLatency
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
                                                                                                [0],
                                                                                                [owner_pp_size], 3)
            iot_device_time_consumed += duration

            iot_device_power_consumed += self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(0, 0.1,
                                                                                                                1,
                                                                                                                [0],
                                                                                                                [
                                                                                                                    owner_pp_size],
                                                                                                                3) / duration

            # user receives the PP of the owner
            duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(0, 0.1, 1,
                                                                                                [owner_pp_size],
                                                                                                [0], 3)
            u.add_to_time_spent(duration)

            u.add_to_power_consumed(self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(0, 0.1, 1,
                                                                                                           [
                                                                                                               owner_pp_size],
                                                                                                           [0],
                                                                                                           3) / duration)

            if u.consent == 1:
                # user sends the consent to the owner
                # indicated by reply of the same PP as received
                duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                    [0],
                                                                                                    [owner_pp_size], 3)

                u.add_to_time_spent(duration)
                iot_device_time_consumed += duration

                iot_device_power_consumed += self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(0,
                                                                                                                    0.1,
                                                                                                                    1,
                                                                                                                    [
                                                                                                                        owner_pp_size],
                                                                                                                    [0],
                                                                                                                    3) / duration

                u.add_to_power_consumed(
                    self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                           [owner_pp_size],
                                                                                           [owner_pp_size],
                                                                                           3) / duration)

            elif u.consent == 2:
                # user forwards its PP to the iot
                # the owner then forwards "modified" PP to the user
                # we just assume it is the same as the PP sent to the user
                duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                    [owner_pp_size],
                                                                                                    [user_pp_size], 3)
                u.add_to_time_spent(duration)

                u.add_to_power_consumed(
                    self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                           [owner_pp_size],
                                                                                           [user_pp_size],
                                                                                           3) / duration)

                duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                    [user_pp_size],
                                                                                                    [owner_pp_size],
                                                                                                    3)
                iot_device_time_consumed += duration

                iot_device_power_consumed += self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(0,
                                                                                                                    0.1,
                                                                                                                    1,
                                                                                                                    [
                                                                                                                        user_pp_size],
                                                                                                                    [
                                                                                                                        owner_pp_size],
                                                                                                                    3) / duration

            elif u.consent > 2:
                logging.error("Invalid consent value in cunche.py.")
                sys.exit(1)

        voltage = 3.3  # We assume that BLE devices operate at 3.3V
        # convert from As to Ws
        u.power_consumed = u.power_consumed * voltage
        iot_device.add_to_power_consumed(iot_device_power_consumed * voltage)
        iot_device.add_to_time_spent(iot_device_time_consumed)

    def zigbee_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        ZigBee-based Cunche negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT Device.
        :return: Power and time consumption of user and iot device.
        """

        # has to be local not to double count
        iot_device_power_consumed = 0
        iot_device_time_consumed = 0

        print("Zigbee Negotation Started")

        # if 0 phases (won't consent) we don't do anything
        # if 1 phase
        if u.consent > 0:
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

            # Send ACK
            charge_tx, d_tx = self.network.network_impl.send(self.network.network_impl.ack_size)
            charge_rx, d_rx = self.network.network_impl.receive(self.network.network_impl.ack_size)

            u.add_to_time_spent(d_rx)
            iot_device_time_consumed += d_tx
            u.add_to_power_consumed(charge_rx)
            iot_device_power_consumed += charge_tx

            if u.consent == 1:
                # the mote sends its consent to the Coordinator
                # indicated by reply of the same PP

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

        elif u.consent == 2:
            # the mote sends its PP to the Coordinator

            charge_tx, d_tx = self.network.network_impl.send(user_pp_size)
            charge_rx, d_rx = self.network.network_impl.receive(user_pp_size)

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

            # the Coordinator sends the "modified" PP to the mote
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

        elif u.consent > 2:
            logging.info("Invalid consent value in cunche.py.")
            sys.exit(1)

        print("Power consumed: ", iot_device_power_consumed)
        iot_device.add_to_time_spent(iot_device_time_consumed)
        iot_device.add_to_power_consumed(iot_device_power_consumed)

    def lora_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        LoRa-based Cunche negotiation implementation.
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
        if u.consent > 0:
            # IoT device (owner) sends PP to the LoRa node (user)

            power_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            u.add_to_time_spent(d_rx)
            iot_device_time_consumed += d_tx
            u.add_to_power_consumed(power_rx)
            iot_device_power_consumed += power_tx

            if u.consent == 1:
                # the LoRa node replies with consent (owner/received PP)
                power_tx, d_tx = self.network.network_impl.send(owner_pp_size)
                power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

                u.add_to_time_spent(d_tx)
                iot_device_time_consumed += d_rx
                u.add_to_power_consumed(power_tx)
                iot_device_power_consumed += power_rx
            elif u.consent == 2:
                # the LoRa node replies with its PP
                power_tx, d_tx = self.network.network_impl.send(user_pp_size)
                power_rx, d_rx = self.network.network_impl.receive(user_pp_size)

                u.add_to_time_spent(d_tx)
                iot_device_time_consumed += d_rx
                u.add_to_power_consumed(power_tx)
                iot_device_power_consumed += power_rx

                # the IoT device replies with "modified" PP
                # for now we simply keep it same as owner PP size
                power_tx, d_tx = self.network.network_impl.send(owner_pp_size)
                power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

                u.add_to_time_spent(d_rx)
                iot_device_time_consumed += d_tx
                u.add_to_power_consumed(power_rx)
                iot_device_power_consumed += power_tx
            elif u.consent > 2:
                logging.error("Invalid consent value in cunche.py.")
                sys.exit(1)

        iot_device.add_to_power_consumed(iot_device_power_consumed)
        iot_device.add_to_time_spent(iot_device_time_consumed)
