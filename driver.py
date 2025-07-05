import numpy as np
from tqdm import tqdm
import logging
from util import check_distance


class Driver:
    """
    The simulation driver class. Responsible for moving time and events forward.
    """

    def __init__(self, scenario, negotiation_protocol):
        """
        Initializes the driver class.
        :param scenario: Scenario to be simulated.
        :param negotiation_protocol: Negotiation protocol to be used.
        """
        self.scenario = scenario
        self.negotiation_protocol = negotiation_protocol

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
        old_t = self.scenario.list_of_users[uur].arr_time
        # Append the first user to the list of current users
        curr_users_list.append(self.scenario.list_of_users[uur])

        distance = 0  # local variable used to update users location

        logging.debug("Total Number of Users: " + str(len(self.scenario.list_of_users)))

        # Uncomment to plot scenario
        # self.scenario.plot_scenario()

        # Extract and flatten the times
        times_list = [(u.arr_time, u.within_comm_range_time) for u in self.scenario.list_of_users]
        flat_times_list = [time for times in times_list for time in times]
        # cleanup
        flat_times_list = list(filter(lambda time: time != 0.0, flat_times_list))

        # Sort the list of times
        sorted_times_list = sorted(flat_times_list)

        # Find the maximum dep_time
        end_time = max(u.dep_time for u in self.scenario.list_of_users if u.dep_time != 0.0)

        # Create progress bar
        pbar = tqdm(total=end_time, colour='green')

        logging.debug("Sorted Simulation Times Queue: " + str(sorted_times_list))

        for curr_t in sorted_times_list:
            # Update progress bar
            pbar.update(curr_t - old_t)

            # determine which users are in the env
            curr_users_list = [u for u in self.scenario.list_of_users if u.arr_time <= curr_t < u.dep_time]

            logging.debug("#################################################################")
            logging.debug("Current time: " + str(curr_t))
            logging.debug("Current before removal users: " + str(len(curr_users_list)))
            logging.debug("User details (id, consent, within_comm_range): " +
                          str([(u.id_, u.consent, u.within_comm_range_time) for u in curr_users_list]))

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

            # Run negotiation for the current users and time
            self.negotiation_protocol.run(curr_users_list, self.scenario.iot_device)

            # for progress bar increment calculation
            old_t = curr_t

            logging.debug(
                "Users within space: " + str([u.id_ for u in curr_users_list if check_distance(u.curr_loc, distance)]))
            logging.debug("List of consented: " + str([u.id_ for u in self.scenario.list_of_users if u.consent >= 1]))
            logging.debug(
                "Total user power consumption: " + str(sum([u.power_consumed for u in self.scenario.list_of_users])))

        # Final update of the progress bar
        pbar.update(curr_t)
        pbar.close()

        # Calculate the statistics
        total_consented = len([u for u in self.scenario.list_of_users if u.consent >= 1])
        avg_user_power_consumption = (sum([u.power_consumed for u in self.scenario.list_of_users]) /
                                      len(self.scenario.list_of_users))

        total_owner_power_consumption = self.scenario.iot_device.power_consumed
        avg_user_time_spent = (sum([u.time_spent for u in self.scenario.list_of_users]) /
                               len(self.scenario.list_of_users))
        total_owner_time_spent = self.scenario.iot_device.time_spent

        return total_consented, avg_user_power_consumption, total_owner_power_consumption, \
            avg_user_time_spent, total_owner_time_spent, curr_t, self.scenario.list_of_users, self.scenario.iot_device
