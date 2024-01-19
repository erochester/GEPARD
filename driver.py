import numpy as np
from tqdm import tqdm


class Driver:
    """
    The simulation driver class. Responsible for moving time and events forward.
    """
    def __init__(self, scenario, negotiation_protocol, logger):
        """
        Initializes the driver class.
        :param scenario: Scenario to be simulated.
        :param negotiation_protocol: Negotiation protocol/algorithm to be used.
        :param logger: Logger object.
        """
        self.scenario = scenario
        self.negotiation_protocol = negotiation_protocol
        self.logger = logger

    def run(self):
        """
        The main method of the driver that moves the time and events forward.
        :return: Returns power and time consumption, user consents, and updated scenario objects.
        """
        # Current user list
        curr_users_list = []

        # User under review
        uur = 0
        # Current time is the arrival time of the first user (1st event)
        curr_t = self.scenario.list_of_users[uur].arr_time
        # Append the first user to the list of current users
        curr_users_list.append(self.scenario.list_of_users[uur])

        total_user_power_consumption = 0  # defines the total power consumption of the user
        total_owner_power_consumption = 0  # defines the total power consumption of the owner
        total_user_time_spent = 0  # defines the total time spent by the user
        total_owner_time_spent = 0  # defines the total time spent by the owner
        total_consented = 0  # defines the number of users that consented

        self.logger.debug("Total Number of Users: " + str(len(self.scenario.list_of_users)))

        # self.scenario.plot_scenario()

        # Create progress bar
        end_time = self.scenario.list_of_users[len(self.scenario.list_of_users) - 1].dep_time
        pbar = tqdm(total=end_time, colour='green')

        # Run the simulation until we run out of the users/time
        while curr_t <= self.scenario.list_of_users[len(self.scenario.list_of_users) - 1].dep_time:

            self.logger.debug("#################################################################")
            self.logger.debug("Current time: " + str(curr_t))
            self.logger.debug("Current before removal users: " + str(len(curr_users_list)))

            # Update current user list (remove the ones that have left the area)
            for u in curr_users_list:
                if u.dep_time <= curr_t:
                    curr_users_list.remove(u)

            self.logger.debug("Current after removal users: " + str(len(curr_users_list)))

            for u in curr_users_list:
                if u.consent:
                    curr_users_list.remove(u)

            self.logger.debug("Current after removal of consented users: " + str(len(curr_users_list)))

            # Update current user location
            for u in curr_users_list:
                distance = np.sqrt(
                    (u.arr_loc[0] - u.dep_loc[0]) ** 2
                    + (u.arr_loc[1] - u.dep_loc[1]) ** 2
                )
                d_coeff = ((curr_t - u.arr_time) * u.speed) / distance
                u.update_location(
                    (
                        ((1 - d_coeff) * u.arr_loc[0] + (d_coeff * u.dep_loc[0])),
                        ((1 - d_coeff) * u.arr_loc[1] + (d_coeff * u.dep_loc[1])),
                    )
                )

            user_consent, applicable_users, total_user_power_consumption_tmp, total_owner_power_consumption_tmp, \
                total_user_time_spent_tmp, total_owner_time_spent_tmp = \
                self.negotiation_protocol.run(curr_users_list, self.scenario.iot_device)

            self.logger.debug("Users in range: " + str(applicable_users))
            self.logger.debug("List of consented: " + str([x for x in user_consent if x.id_]))
            self.logger.debug("Consented: " + str(len([x for x in user_consent if x.consent])))
            self.logger.debug("User power consumption: " + str(total_user_power_consumption_tmp))
            self.logger.debug("Owner power consumption: " + str(total_owner_power_consumption_tmp))

            total_consented += len([x for x in user_consent if x.consent])
            total_user_power_consumption += total_user_power_consumption_tmp
            total_owner_power_consumption += total_owner_power_consumption_tmp
            total_user_time_spent += total_user_time_spent_tmp
            total_owner_time_spent += total_owner_time_spent_tmp

            # Go to the next user under review
            uur += 1

            self.logger.debug("Users left: " + str(len(curr_users_list)))
            # If there are no users left, we break out of simulation loop
            if not curr_users_list:
                break

            self.logger.debug("No more arrivals left?: " + str(uur >= len(self.scenario.list_of_users)))
            # if this is the last arriving user
            if uur >= len(self.scenario.list_of_users):
                min_dep_time = min(curr_users_list, key=lambda x: x.dep_time).dep_time
                # Update progress bar
                pbar.update(min_dep_time - curr_t)
                curr_t = min_dep_time
            # otherwise we continue to update arriving, estimating their privacy coefficients and
            # adding to the current user list
            else:
                # Update progress bar
                pbar.update(self.scenario.list_of_users[uur].arr_time - curr_t)
                curr_t = self.scenario.list_of_users[uur].arr_time
                curr_users_list.append(self.scenario.list_of_users[uur])

        # Final update of the progress bar
        pbar.update(curr_t)
        pbar.close()

        return total_consented, total_user_power_consumption, total_owner_power_consumption, \
            total_user_time_spent, total_owner_time_spent, curr_t, self.scenario.list_of_users, self.scenario.iot_device
