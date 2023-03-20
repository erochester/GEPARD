from util import check_distance
import random


class Alanezi:

    def __init__(self, network):
        self.network = network

    def run(self, curr_users_list):
        # list of consented users
        user_consent = []

        # FIXME: For now we assume 217 and 639 bytes the sizes of PP (should be dynamic?)
        user_pp_size = 217
        owner_pp_size = 639

        total_user_power_consumption = 0
        total_owner_power_consumption = 0

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
        distance = 40
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
                    util = -gamma * priv_policy[0] * priv_policy[1] * priv_policy[2] * priv_policy[3] + \
                           sum(list(priv_policy))
                    if util >= 0:
                        u.update_consent(True)
                        user_consent.append(1)
                    else:
                        user_consent.append(0)
                elif u.privacy_label == 2:
                    # for pragmatists, we have potentially 2 phase negotiation
                    # we first offer PP3
                    # priv_policy = privacy_dim[2]
                    # as per work gamma is a value in range (0.25, 75]
                    gamma = random.uniform(0.26, 0.75)
                    # if gamma is too large we will not consent
                    if gamma > 0.618:
                        user_consent.append(0)
                    elif gamma > 0.368:
                        # single phase consent
                        u.update_consent(True)
                        user_consent.append(1)
                    else:
                        # two phase consent
                        u.update_consent(True)
                        user_consent.append(2)
                else:
                    # for unconcerned we always consent with 1 phase
                    u.update_consent(True)
                    user_consent.append(1)

        # Network power consumption calculations
        # now we iterate through user consent and sum up the power consumption
        for u in user_consent:
            # check how many phases in negotiation
            # if 0 we don't do anything
            # if 1 phase
            if u == 1:
                # the user sends the PP to the owner
                # it will take user_pp_packets transmissions on the IoT user side
                total_user_power_consumption += self.network.send(user_pp_size)

                # the owner accepts the PP and starts "relaying" the data or
                # collecting the data, as such the negotiation is done
                total_owner_power_consumption += self.network.receive(user_pp_size)
            # if negotiation is 2 phases
            elif u == 2:
                # in 2 phase negotiation we start exactly the same way as in 1 phase
                # the user sends the PP to the owner
                # it will take user_pp_packets transmissions on the IoT user side
                total_user_power_consumption += self.network.send(user_pp_size)

                # the owner accepts the PP and starts "relaying" the data or collecting the data,
                # as such the negotiation is done
                total_owner_power_consumption += self.network.receive(user_pp_size)

                # following that, however, the owner sends a different proposal
                total_owner_power_consumption += self.network.send(owner_pp_size)

                # user receives the owner pp
                total_user_power_consumption += self.network.receive(owner_pp_size)

                # the user then sends the reply
                total_user_power_consumption += self.network.send(user_pp_size)

                # owner receives it
                total_owner_power_consumption += self.network.receive(user_pp_size)

        # FIXME: we can also add timing information, but I don't think there is a point in it right now
        # now we can return the number of contacted users, how many consented, after how many rounds and
        # how much energy was consumed
        return user_consent, applicable_users, total_user_power_consumption, total_owner_power_consumption
