import numpy as np
import random
import math
from user import User
from iot_device import IoTDevice

# visualuzation imports
import matplotlib.pyplot as plt
from matplotlib.patches import Circle



class ShoppingMall:

    def __init__(self, list_of_users, iot_device):
        self.list_of_users = list_of_users
        self.iot_device = iot_device

    def generate_scenario(self):
        # The shopping mall works 10 am to 9 pm which results in 11 hours of operation
        # We assume that there are no arrivals in the last hour of operation, so we generate users from 10 am to 8 pm
        # TODO: change to 10*60
        last_arrival = 10

        # Arrival lambda is assumed from shopping mall data analysis papers
        # for now it is set to 2 (meaning 2 users arrive per minute)
        lmbd = 2

        # Initialize arrival time
        arrival_time = 0

        # Initial user id
        user_id = 0

        # The shopping mall IoT device has operational range of 40 meters
        radius = 40

        # New arrivals come until 8 pm
        while arrival_time <= last_arrival:
            # Generate the speed
            speed = np.random.uniform(0.27, 1.5)

            # Generate user arrival angle and calculate coordinates on the sensing disk
            arrival_angle = np.random.rand() * np.pi * 2
            x_a = np.cos(arrival_angle) * radius
            y_a = np.sin(arrival_angle) * radius

            # Generate departure angle and calculate coordinates on the sensing disk
            departure_angle = np.random.rand() * np.pi * 2
            x_d = np.cos(departure_angle) * radius
            y_d = np.sin(departure_angle) * radius

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

            # Create the user and append to the list
            user = User(user_id, speed, (x_a, y_a), (x_d, y_d), privacy_label, privacy_coeff)
            self.list_of_users.append(user)
            user_id += 1

            # Get the next probability value from Uniform(0,1)
            p = random.random()

            # Plug it into the inverse of the CDF of Exponential(_lambda)
            inter_arrival_time = -math.log(1.0 - p) / lmbd

            # Add the inter-arrival time to the arrival time
            arrival_time = arrival_time + inter_arrival_time
            user.updateArrivalTime(arrival_time)

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
            user.updateDepartureTime(departure_time)

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

        plt.show()

