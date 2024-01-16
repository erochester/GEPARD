import random

# visualization imports
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from user import User


class University:

    def __init__(self, list_of_users, iot_device):
        self.list_of_users = list_of_users
        self.iot_device = iot_device
        # TODO: The university radius is assumed to be the middle ground, i.e., 80 meters
        self.radius = 80

    def generate_scenario(self, dist):
        # TAssume university times to be 9 am to 5 pm
        last_arrival = 8 * 60

        # Based on: https://web.archive.org/web/20150216063946id_/http://people.cs.umass.edu:80/~yungchih/publication/Infocom_mobility_queue.pdf
        # The arrival rate between 9 am and 5 pm is the most stable at university
        # We get 14.18 users per minute
        lmbd = 14.18  # base arrival rate per minute

        # Initialize arrival time
        arrival_time = 0

        # Initial user id
        user_id = 0

        # New arrivals come until midnight as we simulate 1 full day
        while arrival_time <= last_arrival:
            # Generate the speed
            # increase speed by 10% as in university people will walk faster
            speed = 1.1 * np.random.uniform(0.27, 1.5)

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

            # Adjust privacy coefficient to be lower since university is less privacy sensitive?
            # TODO: this doesn't seem to have any implications right now
            privacy_coeff = 0.9 * privacy_coeff

            # Define weights for utility calculation
            # for university scenario we assume that energy consumed is more important than service provided for user
            # and that energy consumed is more important than data collected for IoT device
            # first is data/service and second is energy
            weights = [0.2, 0.8]

            self.iot_device.update_weights(weights)

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
            departure_time = arrival_time + (distance / user.speed)
            user.update_departure_time(departure_time)

    def plot_scenario(self):
        fig, ax = plt.subplots()
        plt.rcParams['figure.figsize'] = [4, 4]

        ax.add_patch(Circle((0, 0), 40, edgecolor='blue', facecolor='none', lw=1))
        ax.add_patch(Circle((self.iot_device.device_location[0], self.iot_device.device_location[1]), 2,
                            edgecolor='orange', facecolor='orange', lw=1))
        plt.text(1, 1, "IoT Device")

        ax.scatter(*zip(*[x.arr_loc for x in self.list_of_users]), c='g')
        ax.scatter(*zip(*[x.dep_loc for x in self.list_of_users]), c='r')

        for i in range(len([x.arr_loc for x in self.list_of_users])):
            x_points = ([x.arr_loc for x in self.list_of_users][i][0], [x.dep_loc for x in self.list_of_users][i][0])
            y_points = ([x.arr_loc for x in self.list_of_users][i][1], [x.dep_loc for x in self.list_of_users][i][1])
            plt.plot(x_points, y_points, linestyle='dashed')

        for i, txt in enumerate(["ID: " + str(x.id) for x in self.list_of_users]):
            plt.annotate(txt, (list(zip(*[x.arr_loc for x in self.list_of_users]))[0][i],
                               list(zip(*[x.arr_loc for x in self.list_of_users]))[1][i]))

        # add x and y axis labels
        plt.xlabel("meters (m)")
        plt.ylabel("meters (m)")

        plt.show()
