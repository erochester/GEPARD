import random

# visualization imports
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from user import User
from util import get_config


class ShoppingMall:
    """
    Implements the Shopping Mall scenario.
    """

    def __init__(self, list_of_users, iot_device, network):
        """
        Initializes all the users, the IoT device and the space size for the scenario.
        :param list_of_users: List of all User objects.
        :param iot_device: IoT device object.
        """
        self.config = get_config()['ShoppingMall']  # Load shopping mall-specific config
        self.list_of_users = list_of_users
        self.iot_device = iot_device
        # The radius of the shopping mall is assumed to be 120 meters
        self.radius = self.config['radius']
        self.last_arrival = self.config['last_arrival']
        # Arrival lambda is assumed from shopping mall data analysis papers
        # ref: https://arxiv.org/pdf/1905.13098.pdf
        # customers per min.
        self.lmbd = self.config['lambda']  # User arrival rate per minute
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
        # Initialize arrival time
        arrival_time = 0

        # Initial user id
        user_id = 0

        # New arrivals come until 8 pm
        while arrival_time <= self.last_arrival:
            # Generate the speed (m/min.)
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

                # Calculate the discriminant
                discriminant = B ** 2 - 4 * A * C

                # Initialize the closest point and minimum distance
                closest_point = None
                min_distance = float('inf')
                within_comm_range_time = 0.0

                # Check if the line intersects the inner circle
                if discriminant >= 0:
                    # Calculate the two solutions for t
                    t1 = (-B + np.sqrt(discriminant)) / (2 * A)
                    t2 = (-B - np.sqrt(discriminant)) / (2 * A)

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

            # Define weights for utility calculation
            # for shopping mall scenario we assume that energy consumed is more important than service provided for user
            # but that data collected is more important than energy consumed for IoT device
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
            departure_time = (
                    arrival_time + (distance / user.speed)
            )
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

        # plt.show()
        plt.show()
