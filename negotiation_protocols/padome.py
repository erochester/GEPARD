from concurrent.futures import ThreadPoolExecutor

from util import check_distance, get_distance
import random
import sys
import logging
import numpy as np
import itertools
from util import solve_for_z
from scipy.stats import uniform
import math

from util import get_config


class Padome:
    """
    Implements Padome negotiation protocol. Includes BLE, ZigBee and LoRa based negotiations.
    """

    def __init__(self, network):
        """
        Initializes Padome class.
        :param network: network type (e.g., BLE)
        """
        self.network = network
        self.config = get_config()['Padome']  # load padome config
        self.reservation_value = self.config['reservation_value']
        self.user_pp_size = self.config['user_pp_size']
        self.owner_pp_size = self.config['owner_pp_size']
        self.neg_value = self.config['neg_value']
        self.neg_range = self.config['neg_range']
        self.deadline_factors = {}
        self.privacy_type_distribution = {}
        self.response_likelihood = {}
        self.privacy_weights = {}

    def run(self, curr_users_list, iot_device):
        """
        Main driver for the negotiations. Sets up the main parameter, determines applicable user set for the
        negotiations, calls multiprocessor to run the negotiation matching the network type selected and processes
        the results.
        :param curr_users_list: list of current users in the environment (Users object).
        :param iot_device: IoT device object.
        :return: Returns total device power and time consumption, as well as the updated user lists.
        """

        a, b = np.random.uniform(0, 1, 2)
        a, b = min(a, b), max(a, b)

        # Assume 3 negotiable values, each in range (1-5)
        # (offer, estimated_offer_utility (if elicited then the true utility), probability of acceptance by opponent,
        # elicitation from user state)
        offers = [(o, uniform(loc=a, scale=b - a), np.random.uniform(0, 1), 0)
                  for o in list(itertools.product((range(1, self.neg_range + 1)), repeat=self.neg_value))]

        # For now, we assume that the IoT owner precisely knows the user's privacy preferences and
        #  what to offer to them. We can add the estimator further down the line
        #  for now we go through the list of users, offer to them the privacy policies and
        #  see if they consent and if it is after 1 phase or 2 phases

        # remove users that are > x m away from IoT device (outside the communication range, but not sensing)
        # For example, 50 meters for BLE

        applicable_users = []
        for u in curr_users_list:
            if check_distance(u.curr_loc, self.network.network_impl.comm_distance) and not u.neg_attempted:
                u.offers = offers
                applicable_users.append(u)

        # applicable_users = [u for u in applicable_users if not u.neg_attempted]
        deadline = 0

        if applicable_users:
            # Dynamically calculate the negotiation deadline
            deadline = self.calculate_dynamic_deadline(applicable_users, iot_device, self.user_pp_size,
                                                       self.owner_pp_size)

        for user in applicable_users:
            # for each user determine the number of negotiation rounds based on the proposed negotiation algorithm
            self.negotiation_round_computation(user, iot_device, curr_users_list, self.user_pp_size, deadline)

        # remove users that will not consent
        # applicable_users = [u for u in applicable_users if u.consent > 0]

        logging.debug("Applicable users: %s", [u.id_ for u in applicable_users])

        for _ in applicable_users:
            logging.debug("Applicable users that will consent: %s", [u.id_ for u in applicable_users])

            if applicable_users:
                # Create a list of dictionaries containing arguments for the function
                user_data_list = [{"user_data": user_data, "user_pp_size": self.user_pp_size,
                                   "owner_pp_size": self.owner_pp_size,
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

    def calculate_dynamic_deadline(self, applicable_users, iot_device, user_pp_size, owner_pp_size):
        """
        Calculate the negotiation deadline dynamically based on several factors.
        :param applicable_users: List of users applicable for negotiation.
        :param iot_device: IoT device object.
        :param user_pp_size: User PP size.
        :param owner_pp_size: Owner PP size.
        :return: Returns a dynamically calculated deadline.
        """
        self.deadline_factors = self.config['deadline_factors']
        # Scale deadline by the number of applicable users
        user_count_factor = len(applicable_users) * self.deadline_factors['user_count_factor_multiplier']

        # Network factor based on communication speed
        network_factor = self.deadline_factors['network_factors'].get(self.network,
                                                                      self.deadline_factors['network_factors'][
                                                                          'default'])

        base_deadline = self.deadline_factors['base_deadline']

        # Distance factor: Add more rounds if the average user distance is high
        avg_distance = np.mean([get_distance(u.curr_loc, iot_device.device_location) for u in applicable_users])
        max_comm_distance = self.network.network_impl.comm_distance
        distance_factor = (avg_distance / max_comm_distance) * 2  # Scales up to 2 additional rounds

        # Adjust for user PP sizes if necessary (larger PP = more rounds)
        pp_size_factor = (min(user_pp_size, owner_pp_size) / max(owner_pp_size,
                                                                 user_pp_size)) * 1.5
        # Scales up to 1.5 additional rounds

        # Combine all factors to calculate the deadline
        dynamic_deadline = base_deadline + user_count_factor + network_factor + distance_factor + pp_size_factor

        logging.debug("Dynamic deadline: %s", dynamic_deadline)

        return math.ceil(dynamic_deadline)

    def negotiation_round_computation(self, user, iot_device, curr_users_list, user_pp_size, deadline):
        """
        Method to compute the number of negotiation rounds per user in the environment
        using the proposed negotiation protocols and algorithms
        :param user: current user in the environment (Users object).
        :param iot_device: IoT device object.
        :param curr_users_list: list of current users in the environment (Users object).
        :param user_pp_size: User PP size.
        :param deadline: Deadline for negotiations.
        """

        # Number of rounds
        num_rounds = 0

        dummy_offer = None

        # Find or create the dummy offer ω0 if it's not in the user's offers
        for o in user.offers:
            _, offer_values, _, _ = o
            # Check if offer_values has 'a' and 'b' attributes (i.e., it is a distribution)
            if hasattr(offer_values, 'a') and hasattr(offer_values, 'b'):
                # Perform the range check if offer_values is a distribution
                if offer_values.a <= self.reservation_value <= offer_values.b:
                    dummy_offer = o
                    break
            else:
                # Handle the case where offer_values is a float (no need to check a and b)
                if offer_values <= self.reservation_value:
                    dummy_offer = o
                    break

        if not dummy_offer:
            # Create a dummy offer with utility equal to the reservation value (ω0)
            dummy_offer = (None, self.reservation_value, 0.0, 0)  # Adjust as necessary for your offer format

        offered_before = set()  # Track offers that were previously made

        while num_rounds < deadline:
            # do this until IoT device/user consent, we reach reservation value (rejection) or deadline

            # Step 2: Elicit opponent model and consensus building
            if len(curr_users_list) > 1:
                self.elicit_opponent_model(user, [u for u in curr_users_list if u != user], user_pp_size)

            # Step 3: Elicit user preferences
            self.elicit_user_preferences(user)

            # Step 4: Determine best offer
            # compute the function over values for each variable
            function_values = [
                self.calculate_offer_value(value if elicited else value.rvs(), probability)
                for _, value, probability, elicited in user.offers
            ]
            # Find the index of the maximum value
            argmax_index = np.argmax(function_values)
            # Find the corresponding x value that maximizes the function
            best_offer = user.offers[argmax_index]

            # Step 5: Implement the logic based on the ω = ω0, ACCEPT, or SEND conditions

            # Step 5a: If the best offer is equal to the dummy offer (BREAKOFF)
            # Ensure that best_offer[1] is a float for comparison
            if hasattr(best_offer[1], 'rvs') and hasattr(best_offer[1], 'mean'):
                # You can use the mean of the distribution or sample from it
                offer_value = best_offer[1].mean()  # or best_offer[1].rvs() to sample a random value
            else:
                offer_value = best_offer[1]

            if best_offer == dummy_offer or offer_value <= self.reservation_value:
                user.neg_attempted = True
                logging.debug(f"User {user.id_} broke off negotiations at round {num_rounds}.")
                user.utility = self.reservation_value
                iot_device.utility += self.reservation_value
                break  # End negotiation if the best offer is the dummy offer

            # Step 5b: If the best offer was offered previously (ACCEPT)
            elif best_offer in offered_before:
                # user.accept_offer(best_offer)
                user.utility = offer_value
                iot_device.utility += offer_value
                logging.debug(f"User {user.id_} accepted the offer at round {num_rounds}.")
                user.neg_attempted = True
                break  # End negotiation if the offer is accepted

            # Step 5c: Otherwise, SEND (propose a new offer)
            else:
                logging.debug(f"User {user.id_} sent a new offer at round {num_rounds}.")
                offered_before.add(best_offer)
                user.neg_attempted = True
                # check if the offer will be accepted
                # find best_offer in iot.offers, get its probability and see if will be accepted or rejected
                # (using random.random)
                offer_accepted = self.check_offer(iot_device, best_offer)
                # Here you could add logic to modify or refine the offer based on the negotiation strategy
                if offer_accepted:
                    if hasattr(best_offer[1], 'rvs') and hasattr(best_offer[1], 'mean'):
                        # You can use the mean of the distribution or sample from it
                        offer_value = best_offer[1].mean()  # or best_offer[1].rvs() to sample a random value
                    else:
                        offer_value = best_offer[1]
                    user.utility = offer_value
                    iot_device.utility += offer_value
                    logging.debug(f"IoT device accepted the offer at round {num_rounds}.")
                    break  # End negotiation if the offer is accepted

            # Increment round count
            num_rounds += 1

            # Step 6: If deadline is reached, the negotiation failed
            if num_rounds >= deadline:
                logging.debug(f"Deadline reached for User {user.id_}. Negotiation failed.")
                num_rounds = 0
                break

        # At this point, either negotiation was successful, or the deadline was reached.
        logging.debug(f"Negotiation completed for User {user.id_} in {num_rounds} rounds.")
        # save number of rounds in consent variable
        user.consent = num_rounds

    def calculate_offer_value(self, value, probability):
        """
        Define the function probability*utility + (1 - probability)*aspiration_value
        :param value: Utility/value of an offer.
        :param probability: Probability of offer acceptance.
        :return: Calculated offer value.
        """
        return probability * value + (1 - probability) * self.reservation_value

    def check_offer(self, iot_device, best_offer):
        """
        Function to check if the offer is accepted
        :param iot_device: IoT Device object.
        :param best_offer: Current best offer.
        :return: Check if offer is accepted given the offer probability and a random value.
        """
        # Find best_offer in iot.offers, get its probability and check acceptance
        for offer in iot_device.offers:
            offer_value, offer_probability, offer_elicited = offer
            if offer_value == best_offer:
                if random.random() < offer_probability:
                    return True
                else:
                    return False

    def elicit_opponent_model(self, user, curr_user_list, user_pp_size):
        """
        Determine if we want ot elicit other PAs for opponent's model.
        If yes, elicit the opponent's model from other PAs to better estimate the probability of
        opponent accepting offers.
        :param user_pp_size:
        :param user:
        :param curr_user_list:
        """
        estimated_time_cost_user = 0
        estimated_power_cost_user = 0

        estimated_time_cost_pas = 0
        estimated_power_cost_pas = 0

        # list of PAs that responded
        pas_responded = []
        pa_accounted_for = False

        # Estimate power and time costs of broadcasting the elicitation
        # we compute this as 1 send message and curr_user_list * probability of response * receive
        if self.network.network_type == "ble":
            # Calculate the power consumption and duration for BLE
            # We use device discovery for broadcast. The values are taken from:
            # https://www.researchgate.net/publication/335808941_Connection-less_BLE_Performance_Evaluation_on_Smartphones
            # Request/Response is assumed to be pp size
            result = (self.network.network_impl.discovery.ble_model_discovery_get_result_alanezi
                      (100, 0.9999, 0.25, 5, 2, 0.01, 1000, user_pp_size))

            estimated_time_cost = result.discoveryLatency
            # charge_c is in [C], so we should divide by dc to get the current
            current_c = result.chargeAdv / result.discoveryLatency
            # convert from As to Ws
            estimated_power_cost = current_c

            # send request
            estimated_power_cost_user += estimated_power_cost
            estimated_time_cost_user += estimated_time_cost

            # receive request
            estimated_power_cost_pas += estimated_power_cost
            estimated_time_cost_pas += estimated_time_cost

            # the above only accounts for 1 response
            # we need to add other potential responses
            for u in curr_user_list:
                # for each potential PA determine the response probability based on their user privacy label
                pa_response_probability = random.uniform(0.1, 0.3) if u.privacy_label == 1 \
                    else random.uniform(0.4, 0.6) if u.privacy_label == 2 \
                    else random.uniform(0.7, 0.9)

                if pa_response_probability > random.random() and u.neg_attempted:
                    pas_responded.append(u)

                    duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                        [user_pp_size],
                                                                                                        [0], 3)

                    power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                         [user_pp_size],
                                                                                                         [0], 3)
                    if not pa_accounted_for:
                        # send response
                        estimated_power_cost_pas += power_spent
                        estimated_time_cost_pas += duration
                        pa_accounted_for = True

                    # receive response

                    estimated_power_cost_user += power_spent
                    estimated_time_cost_user += duration

            estimated_power_cost_user = estimated_power_cost_user * self.network.network_impl.voltage
            estimated_power_cost_pas = estimated_power_cost_pas * self.network.network_impl.voltage

        elif self.network.network_type == "zigbee":
            # Calculate the power consumption and duration for Zigbee
            # get the duration and power consumption of startup for the device (Ws, s)
            charge_c, dc = self.network.network_impl.startup()

            estimated_power_cost_pas += charge_c
            estimated_time_cost_pas += dc

            estimated_power_cost_user += charge_c
            estimated_time_cost_user += dc

            # Association duration and power consumption (Ws, s)
            charge_a, da = self.network.network_impl.association()

            estimated_power_cost_pas += charge_a
            estimated_time_cost_pas += da

            estimated_power_cost_user += charge_a
            estimated_time_cost_user += da

            # at the end of association the mote broadcasts
            charge_tx, d_tx = self.network.network_impl.send(user_pp_size)
            estimated_power_cost_user += charge_tx
            estimated_time_cost_user += d_tx

            # receive responses
            charge_rx, d_rx = self.network.network_impl.receive(user_pp_size)

            for u in curr_user_list:
                pa_response_probability = random.uniform(0.1, 0.3) if u.privacy_label == 1 \
                    else random.uniform(0.4, 0.6) if u.privacy_label == 2 \
                    else random.uniform(0.7, 0.9)
                if pa_response_probability > random.random() and u.neg_attempted:
                    if not pa_accounted_for:
                        pa_accounted_for = True

                        estimated_power_cost_pas += charge_rx
                        estimated_time_cost_pas += d_rx

                        estimated_power_cost_pas += charge_tx
                        estimated_time_cost_pas += d_tx

                    pas_responded.append(u)
                    estimated_power_cost_user += charge_rx
                    estimated_time_cost_user += d_rx

        elif self.network.network_type == "lora":
            # Calculate the power consumption and duration for LoRa
            # Broadcast
            power_tx, d_tx = self.network.network_impl.send(user_pp_size)

            estimated_power_cost_user += power_tx
            estimated_time_cost_user += d_tx

            # Reception
            for u in curr_user_list:
                pa_response_probability = random.uniform(0.1, 0.3) if u.privacy_label == 1 \
                    else random.uniform(0.4, 0.6) if u.privacy_label == 2 \
                    else random.uniform(0.7, 0.9)
                if pa_response_probability > random.random() and u.neg_attempted:
                    pas_responded.append(u)
                    power_rx, d_rx = self.network.network_impl.receive(user_pp_size)
                    if not pa_accounted_for:
                        pa_accounted_for = True
                        estimated_power_cost_pas += power_rx
                        estimated_time_cost_pas += d_rx
                        estimated_power_cost_pas += power_tx
                        estimated_time_cost_pas += d_tx

                    estimated_power_cost_user += power_rx
                    estimated_time_cost_user += d_rx
        else:
            # raise error and exit
            logging.error(f"Invalid network type in padome.py: {self.network.network_type}")
            sys.exit(1)

        # Estimate expected information gain based on current users in the environment
        if pas_responded:
            expected_info_gain = self.estimate_information_gain(user, curr_user_list)

            # Compute expected utility of broadcasting
            utility = self.calculate_utility(expected_info_gain, estimated_power_cost_user,
                                             estimated_time_cost_user, user)
        else:
            utility = 0

        # Decision threshold for whether to broadcast  is based on the reservation value
        # less than this utility, and it is not worth it
        if utility > self.reservation_value:
            user.add_to_power_consumed(estimated_power_cost_user)
            user.add_to_time_spent(estimated_time_cost_user)
            # Proceed with broadcasting since utility is above threshold
            responses = {}
            # get the offer we are interested in querying for
            # best_offer = self.get_best_offer(user)
            best_offer = self.max_tuple_by_second_value(user.offers)

            for u in pas_responded:
                u.add_to_power_consumed(estimated_power_cost_pas)
                u.add_to_time_spent(estimated_time_cost_pas)
                responses[u.id_] = self.get_pa_response(best_offer, u) or best_offer[2]

            # Adjust the offer probabilities the user
            for index, offer in enumerate(user.offers):
                if offer[0] == best_offer[0] and len(responses) > 0:
                    # Update the offer probability based on the median approach
                    # it is the most neutral since we don't know the PAs privacy type, and it is robust to outliers
                    sorted_responses = sorted(responses.values())
                    middle = len(sorted_responses) // 2
                    if len(sorted_responses) % 2 == 0:
                        median = (sorted_responses[middle - 1] + sorted_responses[middle]) / 2
                    else:
                        median = sorted_responses[middle]
                    new_probability = (best_offer[2] + median) / 2
                    # Update the offer tuple in user.offers
                    user.offers[index] = (offer[0], offer[1], new_probability, offer[3])

    def calculate_entropy(self, probabilities):
        """Calculate entropy given a list of probabilities."""
        return -sum(p * math.log2(p) for p in probabilities if p > 0)

    def estimate_information_gain(self, user, pas_may_respond):
        """
        Calculate the expected information gain based on the number of PAs in the area.
        :param user: User object.
        :param pas_may_respond: List of PAs that may respond (only length matters here)
        :return: Expected information gain
        """
        # Privacy type distribution (fundamentalist, pragmatist, unconcerned)
        self.privacy_type_distribution = self.config['privacy_type_distribution']

        # Likelihood of responding for each privacy group (follows same distribution as consent probabilities)
        self.response_likelihood = self.config['response_likelihood']

        # Retrieve the privacy type distribution for fundamentalists, pragmatists, unconcerned
        privacy_type_probs = [
            self.privacy_type_distribution['fundamentalist'],
            self.privacy_type_distribution['pragmatist'],
            self.privacy_type_distribution['unconcerned']
        ]

        # Retrieve the response likelihood for fundamentalists, pragmatists, unconcerned
        response_likelihood = [
            self.response_likelihood['fundamentalist'],
            self.response_likelihood['pragmatist'],
            self.response_likelihood['unconcerned']
        ]

        # Step 1: Calculate initial entropy based on privacy type distribution
        # The offer probabilities are provided by the user (this should be part of the offer structure)
        offer_probs = [offer[2] for offer in user.offers]
        initial_entropy = self.calculate_entropy(offer_probs)

        # Step 2: Adjust N based on expected responses from each privacy group
        N_total = len(pas_may_respond)

        if N_total == 0:
            # No PAs in the area, no information gain
            return 0

        # Estimate the expected number of responses based on privacy type distribution and response likelihood
        expected_responses = sum(p * r * N_total for p, r in zip(privacy_type_probs, response_likelihood))

        if expected_responses == 0:
            # No expected responses, no information gain
            return 0

        # Step 3: Estimate new entropy after receiving responses from expected_responses PAs
        # Assuming entropy decreases with more responses but at a diminishing rate
        new_entropy = initial_entropy * (1 / (expected_responses + 1))

        # Step 4: Calculate expected information gain
        information_gain = initial_entropy - new_entropy

        return information_gain

    def calculate_utility(self, expected_info_gain, power_cost, time_cost, user):
        """
        Calculate the utility of broadcasting based on expected information gain and costs.
        """
        # Example utility function: information gain minus weighted costs
        # Assuming energy is more important than time
        utility = expected_info_gain - (user.weights[0] * np.log(1 + time_cost) /
                                        user.weights[1] * np.log(1 + power_cost))
        return utility

    def get_pa_response(self, offer, pa):
        """
        Given an offer and a PA's list of offers, return the probability of acceptance for the matching offer.

        :param pa: The PA whose offers are being searched.
        :param offer: A tuple representing the offer to find.
        :return: The probability of acceptance by the opponent if the offer is found, otherwise None.
        """
        for offer_tuple in pa.offers:
            # Compare the 'offer' component of both tuples
            if offer_tuple[0] == offer[0]:
                # Return the probability of acceptance by opponent (third element in the tuple)
                return offer_tuple[2]
        # If no matching offer is found, return None
        return None

    def max_tuple_by_second_value(self, tuples_list):
        """
        Returns the tuple with the maximum value in the second position.

        :param tuples_list: List of tuples where the second element can be a float or a uniform distribution.
        :return: Tuple with the maximum value in the second position.
        """

        def extract_value(tup):
            """Extracts the value for comparison from the second position."""
            value = tup[1]
            if isinstance(value, float):
                return value
            elif hasattr(value, 'rvs') and hasattr(value, 'mean'):
                # Return the mean of the uniform distribution for comparison
                return value.mean()  # Or you could use value.rvs() for random sampling
            else:
                raise ValueError("The second element must be either a float or a uniform distribution.")

        # Use max with a custom key function to get the tuple with the maximum value in the second position
        return max(tuples_list, key=extract_value)

    def elicit_user_preferences(self, user):
        """
        Determine if we want ot elicit user for user's preferences (determine the real utility of an offer).
        If yes, elicit the user preferences.
        :param user: current user in the environment (Users object).
        """

        c_w = self.config['user_elicitation_cost']

        unelicited_offers = [offer for offer in user.offers if not offer[3]]  # Only offers that haven't been elicited
        elicitation_cost = 0
        v = float('-inf')  # Initialize max utility

        # Step 1: Solve for z for each unelicited offer
        z_values = {}
        for offer, offer_values, probability_of_acceptance, elicitation_status in unelicited_offers:
            # Assuming you calculate the utility based on the offer values (you may need to adjust this)
            z = solve_for_z(offer_values.a, offer_values.b, c_w)  # Adjust 'solve_for_z' as per your logic
            z_values[(offer, offer_values, probability_of_acceptance, elicitation_status)] = z

            # Step 2: Compute initial v value
        for offer, offer_values, probability_of_acceptance, elicitation_status in user.offers:
            # Assuming utility is derived from offer_values; adjust this part if needed
            if hasattr(offer_values, 'rvs'):
                # If it's a distribution (it has .rvs() method)
                utility = offer_values.rvs()
            else:
                # If it's a float or already elicited value
                utility = offer_values
            v = max(v, probability_of_acceptance * utility + (1 - probability_of_acceptance) * c_w)

        # Step 3: Begin elicitation loop
        while unelicited_offers:
            # Find the offer that maximizes z
            best_offer = max(z_values, key=z_values.get)
            max_z = z_values[best_offer]

            # Extract probability_of_acceptance and utility for best_offer[0]
            probability_of_acceptance = best_offer[2]  # This is the second element in the tuple
            utility = best_offer[1].rvs()  # Calculate utility based on offer_values (best_offer[0])

            # Compute the negotiation value based on the given formula
            negotiation_value = probability_of_acceptance * utility + (1 - probability_of_acceptance) * c_w
            # Check stopping condition
            if max_z < negotiation_value or not unelicited_offers:
                return v, elicitation_cost

            # Elicit user preference for the selected offer
            elicited_value = self.elicit_from_user(user, best_offer[0])  # Pass only the offer values for elicitation

            # Update elicitation cost
            elicitation_cost += c_w

            # Remove the best offer from the unelicited list
            unelicited_offers.remove(best_offer)
            z_values.pop(best_offer)

            # Update elicitation status and value in the user's offers list
            for idx, offer in enumerate(user.offers):
                if offer == best_offer:
                    user.offers[idx] = (offer[0], elicited_value, offer[2], True)  # Update elicitation status to True

            # Update v with the new elicited preference
            probability_of_acceptance, utility = best_offer[2], best_offer[1]
            v = max(v, probability_of_acceptance * utility.rvs() + (1 - probability_of_acceptance) * c_w)

            # check if it is "worth" eliciting further
            if elicitation_cost > self.reservation_value:
                break

        # return v, elicitation_cost
        user.utility -= elicitation_cost

    def elicit_from_user(self, user, offer):
        """
        Simulate eliciting user preference for a given offer.
        """
        # Here you can implement the actual user interaction logic
        # For now, we'll assume it returns a random utility value or mock value
        # Example: Return some mock value (in a real scenario, you would elicit from the user)
        # Weights for the privacy factors [data_collection, data_retention, data_sharing] based on user type
        self.privacy_weights = self.config['privacy_weights']
        weights = {
            3: self.privacy_weights['unconcerned'],  # Privacy label 3: Unconcerned
            2: self.privacy_weights['pragmatist'],  # Privacy label 2: Pragmatist
            1: self.privacy_weights['fundamentalist']  # Privacy label 1: Fundamentalist
        }

        # Extract the offer components
        o1, o2, o3 = offer

        # Get the appropriate weight set based on the user's privacy type
        if user.privacy_label in weights:
            w1, w2, w3 = weights[user.privacy_label]
        else:
            raise ValueError("Unknown privacy label for user")

        # Calculate the utility based on the offer and user preferences
        utility = (w1 * o1) + (w2 * o2) + (w3 * o3)

        return utility

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
                # Calculate the power consumption and duration for Zigbee
                self.zigbee_negotiation(user_pp_size, owner_pp_size, u, iot_device)
            elif self.network.network_type == "lora":
                # Calculate the power consumption and duration for LoRa
                self.lora_negotiation(user_pp_size, owner_pp_size, u, iot_device)
            else:
                # raise error and exit
                logging.error("Invalid network type in padome.py.")
                sys.exit(1)

            # Calculate user and owner utility
            # u.add_to_utility(calc_utility(calc_time_remaining(u), u.power_consumed,
            #                               u.weights))
            # Use the user remaining time to calculate the IoT device utility,
            # since the user is moving away (not the device)
            # iot_device.add_to_utility(calc_utility(calc_time_remaining(u),
            #                                        iot_device.power_consumed, iot_device.weights))
            if iot_device.utility == float("inf"):
                # raise error and exit
                logging.error("Got infinite utility for IoT device in padome.py.")
                sys.exit(-1)

    def ble_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        BLE-based Padome negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT device object.
        :return: Power and time consumption of user and iot device.
        """

        # Padome's proposed negotiation follows the following flow:
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
        if u.consent == 1:
            result = (self.network.network_impl.discovery.ble_model_discovery_get_result_alanezi
                      (100, 0.9999, 0.25, 5, 2, 0.01, 1000, user_pp_size))
        else:
            result = (self.network.network_impl.discovery.ble_model_discovery_get_result
                      (100, 0.9999, 0.25, 5, 2, 0.01, 1000))

        u.add_to_time_spent(result.discoveryLatency)
        iot_device_time_consumed += result.discoveryLatency
        # charge_c is in [C], so we should divide by dc to get the current
        current_c = result.chargeAdv / result.discoveryLatency
        u.add_to_power_consumed(current_c)
        iot_device_power_consumed += current_c

        connection_established = False

        # if owner accepts in 1-phase then owner starts sending/collecting the data, and we are done
        # exchanged during device discovery phase
        # if negotiation is more phases
        # if negotiation has more phases
        num_rounds = 1
        if u.consent > 1:
            while u.consent >= num_rounds:
                if not connection_established:
                    duration = \
                        (
                            self.network.network_impl.connection_establishment.ble_e_model_ce_get_duration_for_connection_procedure
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
                        (
                            self.network.network_impl.connection_establishment.ble_e_model_ce_get_duration_for_connection_procedure
                            (1, 0, 0,
                             0,
                             0.1))
                    iot_device_time_consumed += duration
                    iot_device_power_consumed += (
                            self.network.network_impl.connection_establishment.ble_e_model_ce_get_charge_for_connection_procedure
                            (1, 0, 0,
                             0,
                             0.1) / duration)

                    connection_established = True
                # in other phases we start exactly the same way as in 1 phase
                # however now the owner responds with an alternative proposal and waits for the user to reply
                # so two more steps are added
                if num_rounds % 2 != 0:
                    duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                        [0],
                                                                                                        [user_pp_size], 3)
                    u.add_to_time_spent(duration)

                    power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                         [0],
                                                                                                         [user_pp_size], 3)
                    u.add_to_power_consumed(power_spent / duration)
                    duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                        [user_pp_size],
                                                                                                        [0], 3)
                    power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                         [user_pp_size],
                                                                                                         [0], 3)
                    iot_device_time_consumed += duration
                    iot_device_power_consumed += (power_spent / duration)

                else:
                    # in 2 phase negotiation we start exactly the same way as in 1 phase
                    # however now the owner responds with an alternative proposal and waits for the user to reply
                    # so two more steps are added

                    # Note that we assume that there is no delay between connection establishment and sending first packet
                    # after connection establishment the owner sends the proposal and the user receives it
                    # We assume that the user reply is the received PP
                    # we call from master point of view because it has Tx first and then Rx which better simulates the behaviour
                    duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                        [0],
                                                                                                        [owner_pp_size], 3)

                    iot_device_time_consumed += duration

                    power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                         [0],
                                                                                                         [owner_pp_size], 3)
                    iot_device_power_consumed += (power_spent / duration)
                    duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                        [owner_pp_size],
                                                                                                        [0], 3)
                    power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                         [owner_pp_size],
                                                                                                         [0], 3)
                    u.add_to_power_consumed(power_spent / duration)
                    u.add_to_time_spent(duration)

                if u.consent >= num_rounds + 1:
                    num_rounds += 1
                else:
                    break

        # Acceptance

            if num_rounds % 2 != 0:
                duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                    [0],
                                                                                                    [user_pp_size], 3)

                iot_device_time_consumed += duration

                power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                     [0],
                                                                                                     [user_pp_size], 3)
                iot_device_power_consumed += (power_spent / duration)
                duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                    [user_pp_size],
                                                                                                    [0], 3)
                power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                     [user_pp_size],
                                                                                                     [0], 3)
                u.add_to_power_consumed(power_spent / duration)
                u.add_to_time_spent(duration)

            else:
                duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                    [0],
                                                                                                    [owner_pp_size], 3)
                u.add_to_time_spent(duration)

                power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                     [0],
                                                                                                     [owner_pp_size], 3)
                u.add_to_power_consumed(power_spent / duration)
                duration = self.network.network_impl.connected.ble_e_model_c_get_duration_sequences(1, 0.1, 1,
                                                                                                    [owner_pp_size],
                                                                                                    [0], 3)
                power_spent = self.network.network_impl.connected.ble_e_model_c_get_charge_sequences(1, 0.1, 1,
                                                                                                     [owner_pp_size],
                                                                                                     [0], 3)
                iot_device_power_consumed += (power_spent / duration)
                iot_device_time_consumed += duration

        # convert from As to Ws
        u.power_consumed = u.power_consumed * self.network.network_impl.voltage
        iot_device.add_to_power_consumed(iot_device_power_consumed * self.network.network_impl.voltage)
        iot_device.add_to_time_spent(iot_device_time_consumed)

    def zigbee_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        ZigBee-based Padome negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT device object.
        :return: Power and time consumption of user and iot device.
        """

        # Padome's proposed negotiation follows the following flow:
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

        # if negotiation has more phases
        num_rounds = 2
        while u.consent >= num_rounds:
            # in other phases we start exactly the same way as in 1 phase
            # however now the owner responds with an alternative proposal and waits for the user to reply
            # so two more steps are added
            if num_rounds % 2 != 0:
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

                u.add_to_time_spent(d_rx)
                iot_device_time_consumed += d_tx
                u.add_to_power_consumed(charge_rx)
                iot_device_power_consumed += charge_tx
            else:
                # in other phases we start exactly the same way as in 1 phase
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

            if u.consent >= num_rounds + 1:
                num_rounds += 1
            else:
                break

        # Acceptance
        if num_rounds % 2 != 0 or u.consent == 1:
            charge_tx, d_tx = self.network.network_impl.send(user_pp_size)
            charge_rx, d_rx = self.network.network_impl.receive(user_pp_size)

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
        else:
            charge_tx, d_tx = self.network.network_impl.send(owner_pp_size)
            charge_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

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

        iot_device.add_to_time_spent(iot_device_time_consumed)
        iot_device.add_to_power_consumed(iot_device_power_consumed)

    def lora_negotiation(self, user_pp_size, owner_pp_size, u, iot_device):
        """
        LoRa-based Padome negotiation implementation.
        :param user_pp_size: User privacy policy size in bytes.
        :param owner_pp_size: User privacy policy size in bytes.
        :param u: Current user under negotiation.
        :param iot_device: IoT device object.
        :return: Power and time consumption of user and iot device.
        """

        # Padome's proposed negotiation follows the following flow:
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

        # if negotiation has more phases
        num_rounds = 2
        while u.consent >= num_rounds:
            # in other phases we start exactly the same way as in 1 phase
            # however now the owner responds with an alternative proposal and waits for the user to reply
            # so two more steps are added
            if num_rounds % 2 != 0:

                # LoRa node sends alternative offer
                power_rx, d_rx = self.network.network_impl.receive(user_pp_size)

                # Gateway (owner) receives
                power_tx, d_tx = self.network.network_impl.send(user_pp_size)

                u.add_to_time_spent(d_tx)
                iot_device_time_consumed += d_rx
                u.add_to_power_consumed(power_tx)
                iot_device_power_consumed += power_rx

            else:
                # Gateway (owner) sends alternative offer
                power_tx, d_tx = self.network.network_impl.send(owner_pp_size)

                # LoRa node reception
                power_rx, d_rx = self.network.network_impl.receive(owner_pp_size)

                u.add_to_time_spent(d_rx)
                iot_device_time_consumed += d_tx
                u.add_to_power_consumed(power_rx)
                iot_device_power_consumed += power_tx

            if u.consent >= num_rounds+1:
                num_rounds += 1
            else:
                break

        # Acceptance
        if num_rounds % 2 != 0 or u.consent == 1:
            # LoRa device reception
            power_tx, d_tx = self.network.network_impl.send(user_pp_size)

            # Gateway sends same PP
            power_rx, d_rx = self.network.network_impl.receive(user_pp_size)

            u.add_to_time_spent(d_rx)
            iot_device_time_consumed += d_tx
            u.add_to_power_consumed(power_rx)
            iot_device_power_consumed += power_tx

        else:
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
