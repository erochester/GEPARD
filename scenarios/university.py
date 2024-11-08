import random

# visualization imports
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle
from util import get_config

from user import User


class University:
    """
    Implements the Shopping Mall scenario.
    """
    def __init__(self, list_of_users, iot_device, network):
        """
        Initializes all the users, the IoT device and the space size for the scenario.
        :param list_of_users: List of all User objects.
        :param iot_device: IoT device object.
        :param network: Network object to determine the communication range.
        """
        self.config = get_config()['University']  # Load config once
        self.list_of_users = list_of_users
        self.iot_device = iot_device
        # The university radius is assumed to be the middle ground, i.e., 80 meters
        self.radius = self.config['radius']
        # Assume university to work 24/7 (smoothes out the peaks at noon and emptiness at nights)
        self.last_arrival = self.config['last_arrival']
        self.lmbd = self.config['lambda']  # base arrival rate per minute
        self.multiplier = self.config['multiplier']
        self.speed_min = self.config['speed_min']
        self.speed_max = self.config['speed_max']
        self.network = network

    def generate_scenario(self, dist):
        """
        Generates the user object and populates it, i.e., arrival and departure times, privacy preferences, etc.
        Similarly, generates the IoT device object.
        :param dist: Distribution used to generate user inter-arrival events.
        """
        # Based on:
        # http://publications.ics.forth.gr/tech-reports/2006/2006.TR379_Spatio-Temporal_Modeling-WLAN_traffic_demand.pdf
        # (we assume 11 arrivals per hour, as per median, in a single AP (for us IoT device)
        # We get ~0.1833 students per minute


        # Initialize arrival time
        arrival_time = 0

        # Initial user id
        user_id = 0

        while arrival_time <= self.last_arrival:
            # Generate the speed (m/min.)
            # increase speed by 10% as in university people will walk faster
            speed = self.multiplier * np.random.uniform(self.speed_min, self.speed_max)

            # Generate user arrival angle and calculate coordinates on the sensing disk
            arrival_angle = np.random.rand() * np.pi * 2
            x_a = np.cos(arrival_angle) * self.radius
            y_a = np.sin(arrival_angle) * self.radius

            # Generate departure angle and calculate coordinates on the sensing disk
            departure_angle = np.random.rand() * np.pi * 2
            x_d = np.cos(departure_angle) * self.radius
            y_d = np.sin(departure_angle) * self.radius

            within_comm_range_time = 0.0

            if self.radius > self.network.network_impl.comm_distance:
                # Coefficients for the quadratic equation
                A = (x_d - x_a) ** 2 + (y_d - y_a) ** 2
                B = 2 * (x_a * (x_d - x_a) + y_a * (y_d - y_a))
                C = x_a ** 2 + y_a ** 2 - self.network.network_impl.comm_distance ** 2

                # print("Arrival and departure: ", (x_a, y_a), (x_d, y_d))
                # print("A, B and C: ", A, B, C)

                # Calculate the discriminant
                discriminant = B ** 2 - 4 * A * C

                # print("Discriminant: ", discriminant)

                # Initialize the closest point and minimum distance
                closest_point = None
                min_distance = float('inf')

                # Check if the line intersects the inner circle
                if discriminant >= 0:
                    # Calculate the two solutions for t
                    t1 = (-B + np.sqrt(discriminant)) / (2 * A)
                    t2 = (-B - np.sqrt(discriminant)) / (2 * A)

                    # print("T1 and T2: ", t1, t2)

                    intersection_points = []

                    # Check if t1 is within the range [0, 1]
                    if 0 <= t1 <= 1:
                        x1 = x_a + t1 * (x_d - x_a)
                        y1 = y_a + t1 * (y_d - y_a)
                        intersection_points.append((x1, y1))

                    # Check if t2 is within the range [0, 1]
                    if 0 <= t2 <= 1:
                        x2 = x_a + t2 * (x_d - x_a)
                        y2 = y_a + t2 * (y_d - y_a)
                        intersection_points.append((x2, y2))

                    # Determine the closest intersection point to the arrival point
                    for point in intersection_points:
                        distance = np.sqrt((point[0] - x_a) ** 2 + (point[1] - y_a) ** 2)
                        if distance < min_distance:
                            min_distance = distance
                            closest_point = point

                    # print("Intersection points: ", intersection_points)

                    if intersection_points:
                        distance = np.sqrt((closest_point[0] - x_a) ** 2 + (closest_point[1] - y_a) ** 2)
                        within_comm_range_time = distance / speed

            # Privacy fundamentalists (1), privacy pragmatists (2), and privacy unconcerned (3)
            privacy_coeff = random.choice([1] * self.config['privacy_fundamentalists_proportion']
                                          + [2] * self.config['privacy_pragmatists_proportion']
                                          + [3] * self.config['privacy_unconcerned_proportion'])
            if privacy_coeff == 1:
                privacy_coeff = random.uniform(*self.config['privacy_fundamentalists_coeff_range'])
                privacy_label = 1
            elif privacy_coeff == 2:
                privacy_label = 2
                privacy_coeff = random.uniform(*self.config['privacy_pragmatists_coeff_range'])
            else:
                privacy_label = 3
                privacy_coeff = random.uniform(*self.config['privacy_unconcerned_coeff_range'])

            # Adjust privacy coefficient to be lower since university is less privacy sensitive?
            # TODO: this doesn't seem to have any implications right now
            privacy_coeff = self.config['privacy_adjustment_factor'] * privacy_coeff

            # Define weights for utility calculation
            # for university scenario we assume that energy consumed is more important than service provided for user
            # and that energy consumed is more important than data collected for IoT device
            # first is time and second is energy
            weights = [self.config['time_weight'], self.config['energy_weight']]

            self.iot_device.update_weights(weights)

            # Create the user and append to the list
            user = User(user_id, speed, (x_a, y_a), (x_d, y_d), privacy_label, privacy_coeff, weights)
            self.list_of_users.append(user)
            user_id += 1

            inter_arrival_time = dist.generate_random_samples(self.lmbd)

            # Add the inter-arrival time to the arrival time
            arrival_time = arrival_time + inter_arrival_time

            if within_comm_range_time != 0.0:
                user.update_within_comm_range(arrival_time + within_comm_range_time)

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
        """
        Method used to visualize the scenario, i.e., space, user arrival/departure points and
        trajectory across the space.
        """
        fig, ax = plt.subplots()
        plt.rcParams['figure.figsize'] = [4, 4]

        ax.add_patch(Circle((0, 0), self.network.network_impl.comm_distance, edgecolor='blue', facecolor='none', lw=1))
        ax.add_patch(Circle((self.iot_device.device_location[0], self.iot_device.device_location[1]), 2,
                            edgecolor='orange', facecolor='orange', lw=1))
        plt.text(1, 1, "IoT Device")

        ax.scatter(*zip(*[x.arr_loc for x in self.list_of_users]), c='g')
        ax.scatter(*zip(*[x.dep_loc for x in self.list_of_users]), c='r')

        for i in range(len([x.arr_loc for x in self.list_of_users])):
            x_points = ([x.arr_loc for x in self.list_of_users][i][0], [x.dep_loc for x in self.list_of_users][i][0])
            y_points = ([x.arr_loc for x in self.list_of_users][i][1], [x.dep_loc for x in self.list_of_users][i][1])
            plt.plot(x_points, y_points, linestyle='dashed')

        for i, txt in enumerate(["ID: " + str(x.id_) for x in self.list_of_users]):
            plt.annotate(txt, (list(zip(*[x.arr_loc for x in self.list_of_users]))[0][i],
                               list(zip(*[x.arr_loc for x in self.list_of_users]))[1][i]))

        # add x and y axis labels
        plt.xlabel("meters (m)")
        plt.ylabel("meters (m)")

        plt.show()
