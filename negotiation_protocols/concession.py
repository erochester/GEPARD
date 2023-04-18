from util import check_distance, calc_utility, calc_time_remaining
import random
import numpy as np


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
        distance = 40
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
                # the owner sends the PP to the user
                # it will take owner_pp_packets transmissions on the IoT user side
                power_consumed, time_spent = self.network.send(owner_pp_size)
                total_owner_power_consumption += power_consumed
                total_owner_time_spent += time_spent

                # the user receives the PP
                power_consumed, time_spent = self.network.receive(owner_pp_size)
                total_user_power_consumption += power_consumed
                total_user_time_spent += time_spent

                # the user consents
                power_consumed, time_spent = self.network.send(user_pp_size)
                total_user_power_consumption += power_consumed
                total_user_time_spent += time_spent

                # the owner receives consent
                power_consumed, time_spent = self.network.receive(user_pp_size)
                total_owner_power_consumption += power_consumed
                total_owner_time_spent += time_spent

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
