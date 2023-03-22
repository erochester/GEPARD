from util import check_distance
import random


class Cunche:

    def __init__(self, network):
        self.network = network

    def run(self, curr_users_list):
        # list of consented users
        user_consent = []

        user_pp_size = 38
        owner_pp_size = 86

        total_user_power_consumption = 0
        total_owner_power_consumption = 0

        total_user_time_spent = 0
        total_owner_time_spent = 0

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
                        u.update_consent(True)
                        user_consent.append(1)
                    else:
                        user_consent.append(0)
                # everyone else consents
                else:
                    u.update_consent(True)
                    user_consent.append(1)

        # now we iterate through user consent and sum up the power consumption
        for u in user_consent:
            # if 0 we don't do anything
            # if 1 phase
            if u == 1:
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

        return user_consent, applicable_users, total_user_power_consumption, total_owner_power_consumption, \
            total_user_time_spent, total_owner_time_spent
