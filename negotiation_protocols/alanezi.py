from concurrent.futures import ProcessPoolExecutor

from util import check_distance, calc_utility, calc_time_remaining
import random
import sys


class Alanezi:
    """
    Implements Alanezi negotiation algorithm. Includes BLE, ZigBee and LoRa based negotiations.
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
        # list of consented users
        user_consent = []
        user_consent_obj = []

        # FIXME: For now we assume 217 and 639 bytes the sizes of PP (should be dynamic?)
        user_pp_size = 217
        owner_pp_size = 639

        # FIXME: for now we assume that the IoT owner precisely knows the user's privacy preferences and
        #  what to offer to them
        # we can add the estimator further down the line
        # for now we go through the list of users, offer to them the privacy policies and
        # see if they consent and if it is
        # after 1 phase or 2 phases

        # first we define the values for privacy dimensions for different policies
        privacy_dim = [(3, 3, 1, 1), (3, 3, 1, 0), (3, 2, 1, 0), (3, 2, 0, 0)]
        # these are used in calculating utility when offering PP to a user

        # FIXME: change to be dependant on communication technology
        # remove users that are > x m away from IoT device (outside of the communication range, but not sensing)
        # 40 meters for BLE

        applicable_users = []
        # TODO: make distance network dependent
        distance = self.network.network_impl.comm_distance
        for u in curr_users_list:
            if check_distance(u.curr_loc, distance):
                applicable_users.append(u)

        for u in applicable_users:
            # check if user already consented and if not
            if not u.consent:
                # check the user's privacy label
                if u.privacy_label == 1:
                    # for fundamentalists, we offer PP4
                    priv_policy = privacy_dim[3]
                    # as per work gamma is a value in range (0.75,1]
                    gamma = random.uniform(0.76, 1.0)
                    # combination of these values makes sure that only 20.4% of fundamentalists consent
                    util = (-gamma * priv_policy[0] * priv_policy[1] * priv_policy[2] * priv_policy[3] +
                            sum(list(priv_policy)))
                    if util >= 0:
                        u.update_consent(True)
                        user_consent.append(1)
                        user_consent_obj.append(u)
                    else:
                        user_consent.append(0)
                        user_consent_obj.append(u)
                elif u.privacy_label == 2:
                    # for pragmatists, we have potentially 2 phase negotiation
                    # we first offer PP3
                    # priv_policy = privacy_dim[2]
                    # as per work gamma is a value in range (0.25, 75]
                    gamma = random.uniform(0.26, 0.75)
                    # if gamma is too large we will not consent
                    if gamma > 0.618:
                        user_consent.append(0)
                        user_consent_obj.append(u)
                    elif gamma > 0.368:
                        # single phase consent
                        u.update_consent(True)
                        user_consent.append(1)
                        user_consent_obj.append(u)
                    else:
                        # two phase consent
                        u.update_consent(True)
                        user_consent.append(2)
                        user_consent_obj.append(u)
                else:
                    # for unconcerned we always consent with 1 phase
                    u.update_consent(True)
                    user_consent.append(1)
                    user_consent_obj.append(u)
            else:
                # if user already consented we don't do anything
                # shouldn't occur, since we remove all consented users beforehand
                user_consent.append(0)
                user_consent_obj.append(u)

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

        # Remove objects from user_consent_obj that have not consented based on 0 value in user_consent list
        user_consent_obj = [user_consent_obj[i] for i in range(len(user_consent_obj)) if user_consent[i] != 0]

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
        if user_consent[index] == 0:
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
            (curr_user_power_consumption, curr_owner_power_consumption, curr_user_time_spent,
             curr_owner_time_spent) = self.lora_negotiation(user_pp_size, owner_pp_size, u)
        else:
            # raise error and exit
            print("Invalid network type in concession.py.")
            sys.exit(1)

        # Calculate user and owner utility
        user_utility = calc_utility(calc_time_remaining(user_consent_obj[index]), curr_user_power_consumption,
                                    applicable_users[index].weights)
        owner_utility = calc_utility(calc_time_remaining(user_consent_obj[index]),
                                     curr_owner_power_consumption, iot_device.weights)

        # Return the local results
        return (curr_user_power_consumption, curr_user_time_spent, curr_owner_power_consumption, curr_owner_time_spent,
                user_utility, owner_utility)

    def ble_negotiation(self, user_pp_size, owner_pp_size, u):
        """
        BLE-based Alanezi negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :return: Power and time consumption of user and iot device.
        """
        total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent \
            = 0, 0, 0, 0

        # Alanezi's proposed negotiation follows the following flow:
        # BLE broadcast with data request information (user is advertising and IoT owner is scanning, user PP is sent)
        # -> connection establishment -> IoT owner accepts/negotiation -> …done?

        # Consequently, no matter the number of phases the advertising, scanning and connection establishment with
        # at least 1 connection packet always occurs
        # We use the values directly provided by Kindt et al.

        # get the duration of all constant parts of a connection event. (Preprocessing, Postprocessing,...)
        dc = self.network.network_impl.connected.ble_e_model_c_get_duration_constant_parts()

        # now do the same with the charge of these phases
        charge_c = self.network.network_impl.connected.ble_e_model_c_get_charge_constant_parts()

        total_user_time_spent += dc
        total_owner_time_spent += dc
        total_user_power_consumption += charge_c
        total_owner_power_consumption += charge_c

        # print duration and charge of constant parts
        # print("Duration of constant parts: ", dc)
        # print("Charge of constant parts: ", charge_c)

        # Calculate the latency and energy consumption of device discovery. The values are taken from:
        # https://www.researchgate.net/publication/335808941_Connection-less_BLE_Performance_Evaluation_on_Smartphones
        result = (self.network.network_impl.discovery.ble_model_discovery_get_result_alanezi
                  (100, 0.9999, 0.25, 5, 2, 0.01, 1000, user_pp_size))

        total_user_time_spent += result.discoveryLatency
        total_owner_time_spent += result.discoveryLatency
        total_user_power_consumption += result.chargeAdv
        total_owner_power_consumption += result.chargeScan

        # at the end of discovery the device go through connection establishment
        # as per documentation there is no duration, since it is accounted in the discovery
        # For user we set periodic scan type
        total_user_power_consumption += (
            self.network.network_impl.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
            (1, 0, 1,
             0,
             0.1))
        total_owner_power_consumption += (
            self.network.network_impl.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
            (1, 0, 0,
             0,
             0.1))

        # if owner accepts in 1-phase then owner starts sending/collecting the data and we are done

        # if negotiation is 2 phases
        if u == 2:
            # in 2 phase negotiation we start exactly the same way as in 1 phase
            # however now the owner responds with an alternative proposal and waits for the user to reply
            # so two more steps are added

            # Note that we assume that there is no delay between connection establishment and sending first packet
            # after connection establishment the owner sends the proposal and the user receives it
            # FIXME: for now we assume that the user reply is same size as its initial PP size
            # we call from master point of view because it has Tx first and then Rx which better simulates the behaviour
            time_spent = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                  [user_pp_size],
                                                                                                  [owner_pp_size], 3)
            total_user_time_spent += time_spent
            total_owner_time_spent += time_spent

            power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                 [user_pp_size],
                                                                                                 [owner_pp_size], 3)
            total_owner_power_consumption += power_spent

            power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(0, 0.1, 1,
                                                                                                 [owner_pp_size],
                                                                                                 [user_pp_size], 3)
            total_user_power_consumption += power_spent

        return (total_user_power_consumption, total_owner_power_consumption, total_user_time_spent,
                total_owner_time_spent)

    def zigbee_negotiation(self, user_pp_size, owner_pp_size, u):
        """
        ZigBee-based Alanezi negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :return: Power and time consumption of user and iot device.
        """
        total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent \
            = 0, 0, 0, 0

        # Alanezi's proposed negotiation follows the following flow:
        # BLE broadcast with data request information (user is advertising and IoT owner is scanning, user PP is sent)
        # -> connection establishment -> IoT owner accepts/negotiation -> …done?

        # We adjust the negotiation flow to fit Zigbee as follows:
        # ZigBee Mote (user) starts up ->
        # -> Mote associates with the Coordinator (IoT device) -> Mote sends data request information to Coordinator
        # -> Coordinator accepts/negotiation -> ...done?

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

        # at the end of association the mote sends its request to the coordinator
        charge_tx, d_tx = self.network.network_impl.send(user_pp_size)
        charge_rx, d_rx = self.network.network_impl.receive(user_pp_size)

        total_user_time_spent += d_tx
        total_owner_time_spent += d_rx
        total_user_power_consumption += charge_tx
        total_owner_power_consumption += charge_rx

        # the owner also needs to send an ACK to the mote
        # as per: https://github.com/Koenkk/zigbee2mqtt/issues/1455
        # ACK size is 65 bytes

        charge_tx, d_tx = self.network.network_impl.send(self.network.network_impl.ack_size)
        charge_rx, d_rx = self.network.network_impl.receive(self.network.network_impl.ack_size)

        total_user_time_spent += d_rx
        total_owner_time_spent += d_tx
        total_user_power_consumption += charge_rx
        total_owner_power_consumption += charge_tx

        # if owner accepts in 1-phase then owner starts sending/collecting the data and we are done

        # if negotiation is 2 phases
        if u == 2:
            # in 2 phase negotiation we start exactly the same way as in 1 phase
            # however now the owner responds with an alternative proposal and waits for the user to reply
            # so two more steps are added

            # Note that we assume that there is no delay between association and sending first packet
            # after connection establishment the owner sends the proposal and the user receives it
            # FIXME: for now we assume that the user reply is same size as its initial PP size
            charge_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            charge_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            total_user_time_spent += d_rx
            total_owner_time_spent += d_tx
            total_user_power_consumption += charge_rx
            total_owner_power_consumption += charge_tx

            # Send ACK
            charge_tx, d_tx = self.network.network_impl.send(self.network.network_impl.ack_size)
            charge_rx, d_rx = self.network.network_impl.receive(self.network.network_impl.ack_size)

            total_user_time_spent += d_tx
            total_owner_time_spent += d_rx
            total_user_power_consumption += charge_tx
            total_owner_power_consumption += charge_rx

        return total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent

    def lora_negotiation(self, user_pp_size, owner_pp_size, u):
        """
        LoRa-based Alanezi negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :return: Power and time consumption of user and iot device.
        """
        total_user_power_consumption, total_owner_power_consumption, total_user_time_spent, total_owner_time_spent \
            = 0, 0, 0, 0

        # Alanezi's proposed negotiation follows the following flow:
        # BLE broadcast with data request information (user is advertising and IoT owner is scanning, user PP is sent)
        # -> connection establishment -> IoT owner accepts/negotiation -> …done?

        # We adjust the negotiation flow to fit Lora as follows:
        # Class A LoRa node sends data request information to the Gateway
        # -> Gateway accepts/negotiation -> ...done?

        # LoRa device (user) sends its request to the Gateway (owner)
        power_tx, d_tx = self.network.network_impl.send(user_pp_size)

        # Gateway reception
        power_rx, d_rx = self.network.network_impl.receive(user_pp_size)

        total_user_time_spent += d_tx
        total_owner_time_spent += d_rx
        total_user_power_consumption += power_tx
        total_owner_power_consumption += power_rx

        # if owner accepts in 1-phase then owner starts sending/collecting the data and we are done

        # if negotiation is 2 phases
        if u == 2:
            # TODO: For acceptance user replies with its original PP for now
            # in 2 phase negotiation we start exactly the same way as in 1 phase
            # however now the owner responds with an alternative proposal and waits for the user to reply
            # so two more steps are added

            # Gateway (owner) sends alternative offer
            power_tx, d_tx = self.network.network_impl.send(owner_pp_size)

            # LoRa node reception
            power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

            total_user_time_spent += d_tx
            total_owner_time_spent += d_rx
            total_user_power_consumption += power_tx
            total_owner_power_consumption += power_rx

            # Acceptance
            # LoRa device (user) sends its request to the Gateway (owner)
            power_tx, d_tx = self.network.network_impl.send(user_pp_size)

            # Gateway reception
            power_rx, d_rx = self.network.network_impl.receive(user_pp_size)

            total_user_time_spent += d_tx
            total_owner_time_spent += d_rx
            total_user_power_consumption += power_tx
            total_owner_power_consumption += power_rx

        return (total_user_power_consumption, total_owner_power_consumption, total_user_time_spent,
                total_owner_time_spent)
