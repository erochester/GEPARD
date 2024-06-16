import random

# visualization imports
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from user import User


class ShoppingMall:
    """
    Implements the Shopping Mall scenario.
    """

    def __init__(self, list_of_users, iot_device):
        """
        Initializes all the users, the IoT device and the space size for the scenario.
        :param list_of_users: List of all User objects.
        :param iot_device: IoT device object.
        """
        self.list_of_users = list_of_users
        self.iot_device = iot_device
        # The radius of the shopping mall is assumed to be 120 meters
        self.radius = 120

    def generate_scenario(self, dist):
        """
        Generates the user object and populates it, i.e., arrival and departure times, privacy preferences, etc.
        Similarly, generates the IoT device object.
        :param dist: Distribution used to generate user inter-arrival events.
        """
        # The shopping mall works 10 am to 9 pm which results in 11 hours of operation
        # We assume that there are no arrivals in the last hour of operation, so we generate users from 10 am to 8 pm
        last_arrival = 10 * 60

        # Arrival lambda is assumed from shopping mall data analysis papers
        # ref: https://arxiv.org/pdf/1905.13098.pdf
        # customers per min.
        lmbd = 2.55

        # Initialize arrival time
        arrival_time = 0

        # Initial user id
        user_id = 0

        # New arrivals come until 8 pm
        while arrival_time <= last_arrival:
            # Generate the speed (m/min.)
            speed = np.random.uniform(16.2, 90)

            # Generate user arrival angle and calculate coordinates on the sensing disk
            arrival_angle = np.random.rand() * np.pi * 2
            x_a = np.cos(arrival_angle) * self.radius
            y_a = np.sin(arrival_angle) * self.radius

            # Generate departure angle and calculate coordinates on the sensing disk
            departure_angle = np.random.rand() * np.pi * 2
            x_d = np.cos(departure_angle) * self.radius
            y_d = np.sin(departure_angle) * self.radius

            # Privacy fundamentalists (1), privacy pragmatists (2), and privacy unconcerned (3)
            privacy_coeff = random.choice([1] * 25 + [2] * 55 + [3] * 20)
            if privacy_coeff == 1:
                privacy_coeff = random.uniform(0.001, 0.03)
                privacy_label = 1
            elif privacy_coeff == 2:
                privacy_label = 2
                privacy_coeff = random.uniform(0.11, 0.15)
            else:
                privacy_label = 3
                privacy_coeff = random.uniform(0.031, 0.10)

            # Define weights for utility calculation
            # for shopping mall scenario we assume that energy consumed is more important than service provided for user
            # but that data collected is more important than energy consumed for IoT device
            # first is data/service and second is energy
            weights = [0.2, 0.8]

            self.iot_device.update_weights([0.8, 0.2])

            # Create the user and append to the list
            user = User(user_id, speed, (x_a, y_a), (x_d, y_d), privacy_label, privacy_coeff, weights)
            self.list_of_users.append(user)
            user_id += 1

            inter_arrival_time = dist.generate_random_samples(lmbd)

            # Add the inter-arrival time to the arrival time
            arrival_time = arrival_time + inter_arrival_time
            user.update_arrival_time(arrival_time)

            # Calculate distance between user arrival and departure points
            distance = np.sqrt(
                (
                        (user.arr_loc[0] - user.dep_loc[0]) ** 2
                        + (user.arr_loc[1] - user.dep_loc[1]) ** 2
                )
            )
            # Calculate departure time
            departure_time = (
                    arrival_time + (distance / user.speed)
            )
            user.update_departure_time(departure_time)

    def plot_scenario(self):
        """
        Method used to vizualize the scenario, i.e., space, user arrival/departure points and
        trajectory across the space.
        """
        fig, ax = plt.subplots()
        plt.rcParams['figure.figsize'] = [4, 4]

        ax.add_patch(Circle((0, 0), 40, edgecolor='blue', facecolor='none', lw=1))
        ax.add_patch(Circle((self.iot_device.device_location[0], self.iot_device.device_location[1]), 2,
                            edgecolor='orange', facecolor='orange', lw=1))
        plt.text(1, 1, "IoT Device")

        ax.scatter(*zip(*[x.arr_loc for x in self.list_of_users[:10]]), c='g')
        ax.scatter(*zip(*[x.dep_loc for x in self.list_of_users[:10]]), c='r')

        for i in range(len([x.arr_loc for x in self.list_of_users[:10]])):
            x_points = (
                [x.arr_loc for x in self.list_of_users[:10]][i][0], [x.dep_loc for x in self.list_of_users[:10]][i][0])
            y_points = (
                [x.arr_loc for x in self.list_of_users[:10]][i][1], [x.dep_loc for x in self.list_of_users[:10]][i][1])
            plt.plot(x_points, y_points, linestyle='dashed')

        for i, txt in enumerate(["ID: " + str(x.id_) for x in self.list_of_users[:10]]):
            plt.annotate(txt, (list(zip(*[x.arr_loc for x in self.list_of_users[:10]]))[0][i],
                               list(zip(*[x.arr_loc for x in self.list_of_users[:10]]))[1][i]))

        # add x and y axis labels
        plt.xlabel("meters (m)")
        plt.ylabel("meters (m)")

        # plt.show()
        plt.show()
