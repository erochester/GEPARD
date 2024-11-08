import numpy as np
import shutil
import os
import csv
import random
import math
import logging
from scipy.integrate import quad
from scipy.optimize import fsolve
import yaml


# Load configuration from the YAML file only once
def load_config(file_path='config.yaml'):
    with open(file_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config

# Store configuration globally
_config = None

def get_config():
    global _config
    if _config is None:
        _config = load_config()  # Load config on first access
    return _config

def calc_utility(time, energy, weights):
    """
    Calculate the utility of the device
    Use multi-attribute utility function that has been logarithmically transformed (account for time, energy and weights).
    :param time: Represents how long the user will be in environment (s).
    :param energy: Represents current power consumption (W).
    :param weights: Represents the importance of time left vs power consumption.
    :return: Estimated utility.
    """
    k = 100  # scaling factor

    # TODO: added weights[1] see the chnges

    utility = k * (weights[0] * np.log(1 + time) / weights[1] * np.log(1 + energy))
    # utility = k * np.log(1 + time) / np.log(1 + energy) # alternative method for unweighted utility calculations

    return utility


def calc_time_remaining(user):
    """
    Calculate user's time remaining in the environment.
    :param user: User object.
    :return: Remaining time in seconds.
    """

    # Get user's current location
    curr_loc = user.curr_loc
    # Get user's destination
    dest = user.dep_loc
    # Get user's speed
    speed = user.speed

    # Calculate distance between user's current location and destination
    distance = np.sqrt((curr_loc[0] - dest[0]) ** 2 + (curr_loc[1] - dest[1]) ** 2)

    # Calculate time it takes for user to reach destination
    time = distance / speed

    return time


def check_distance(curr_loc, distance):
    """
    Used to see if the user is inside the effective communication range.
    :param curr_loc: User's current location (x,y).
    :param distance: Effective communication range (m).
    :return: Boolean value (True of False).
    """
    # we round due to rounding errors when generating the arrival time to the communication range
    if round(np.sqrt((curr_loc[0] ** 2 + curr_loc[1] ** 2)), 2) > distance:
        return False
    else:
        return True


def get_distance(loc1, loc2):
    """
    Calculates the Euclidean distance between two locations.
    :param loc1: Tuple representing the first location (x1, y1).
    :param loc2: Tuple representing the second location (x2, y2).
    :return: The Euclidean distance between the two locations.
    """
    return round(np.sqrt((loc1[0] - loc2[0]) ** 2 + (loc1[1] - loc2[1]) ** 2), 2)


def result_file_util(filename):
    """
    Utility method for dealing with previously saved results. We can either delete them or create a back-up.
    :param filename: Name of the file to check for existence and make back-up of (if needed).
    """
    # Check if the file exists
    if os.path.isfile(filename):
        # File exists, ask the user what to do
        choice = input(
            f"The file {filename} already exists. "
            f"Do you want to remove it (type 'r') or back it up (type 'b')? ")

        # Remove the file
        if choice.lower() == 'r':
            os.remove(filename)
            logging.info(f"The file {filename} has been removed.")
        # Back up the file
        elif choice.lower() == 'b':
            backup_filename = filename + '.bak'
            shutil.copyfile(filename, backup_filename)
            logging.info(f"The file {filename} has been backed up as {backup_filename}.")
            os.remove(filename)
        # Invalid choice
        else:
            logging.error("Invalid choice.")
            exit(1)


def write_results(filename, rows):
    """
    Method used to write the results of the simulation into the file.
    :param filename: Results file name.
    :param rows: Data to write to the file.
    """
    # Check if the directory exists, if not create it
    directory = os.path.dirname(filename)
    if directory != '' and not os.path.exists(directory):
        create_dir = input(f"The directory {directory} does not exist. Do you want to create it? (y/n): ")
        if create_dir.lower() == 'y':
            os.makedirs(directory)
        else:
            logging.error("The directory does not exist. Please create it and try again.")
            exit(-1)
    # Open a file for writing
    mode = "a" if os.path.exists(filename) else "w"
    with open(filename, mode) as csvfile:
        # Create a CSV writer object
        csvwriter = csv.writer(csvfile)

        # Write the column headers only if the file is newly created
        if mode == "w":
            fields = ["Protocol", "Network", "Scenario", "Avg User Power Consumption (W)",
                      "Total Owner Power Consumption (W)", "Total User Time Spent (s)", "Total Owner Time Spent (s)",
                      "Consent collected from", "Total user number",
                      "Consent Percentage (%)", "Total runtime (min)", "Raw Average User Utility",
                      "Raw Total Owner Utility",
                      "Normalized Average User Utility", "Normalized Total Owner Utility"]
            csvwriter.writerow(fields)

            # Format the data rows to display small values with precision
            formatted_rows = []
            for row in rows:
                formatted_row = [
                    row[0],  # Protocol
                    row[1],  # Network
                    row[2],  # Scenario
                    f"{row[3]:.{determine_decimals(row[3])}f}",  # Avg User Power Consumption (W)
                    f"{row[4]:.{determine_decimals(row[4])}f}",  # Total Owner Power Consumption (W)
                    f"{row[5]:.{determine_decimals(row[5])}f}",  # Total User Time Spent (s)
                    f"{row[6]:.{determine_decimals(row[6])}f}",  # Total Owner Time Spent (s)
                    row[7],  # Consent collected from
                    row[8],  # Total user number
                    f"{row[9]:.{determine_decimals(row[9])}f}",  # Consent Percentage (%)
                    f"{row[10]:.{determine_decimals(row[10])}f}",  # Total runtime (min)
                    f"{row[11]:.{determine_decimals(row[11])}f}",  # Raw Average User Utility
                    f"{row[12]:.{determine_decimals(row[12])}f}",  # Raw Total Owner Utility
                    f"{row[13]:.{determine_decimals(row[13])}f}",  # Normalized Average User Utility
                    f"{row[14]:.{determine_decimals(row[14])}f}"  # Normalized Total Owner Utility
                ]
                formatted_rows.append(formatted_row)

            # Write the formatted data rows
            csvwriter.writerows(formatted_rows)

        # Write the data rows
        csvwriter.writerows(rows)


def determine_decimals(value):
    """
    Determine the number of decimal places based on the magnitude of the value.
    Smaller values get more decimal places.
    :param value: The numeric value.
    :return: Number of decimal places to use for formatting.
    """
    if value == 0:
        return 2  # Avoid log(0) errors
    elif abs(value) >= 1:
        return 2  # For values greater than or equal to 1, use 2 decimal places
    else:
        # For values smaller than 1, use more decimal places based on magnitude
        return min(10, abs(int(np.floor(np.log10(abs(value))))) + 2)


class Distribution():
    """
    Class for different distribution implementation.
    Currently, implements only Poisson arrival process.
    """

    def __init__(self, distribution_type):
        """
        Initialize the Distribution class.
        :param distribution_type: Type of distribution to call.
        """
        self.distribution_type = distribution_type

    def generate_random_samples(self, rate):
        """
        Generate random samples from the specified distribution.
        :param rate: Rate parameter (\lambda in case of Poisson).
        :return: Random inter-arrival time sample.
        """
        if self.distribution_type == "poisson":
            if rate is None:
                raise ValueError("Rate parameter is required for exponential distribution")
            # Poisson process
            # Get the next probability value from Uniform(0,1)
            p = random.random()

            # Plug it into the inverse of the CDF of Exponential(_lambda)
            inter_arrival_time = -math.log(1.0 - p) / rate
            return inter_arrival_time
        else:
            raise ValueError("Unsupported distribution type")


def calc_norm_utility(data, is_iot_device):
    """
    Calculate the normalized utility to make them more comparable.
    :param data: Data to be normalized (either list of user utilities or may include the iot device).
    :param is_iot_device: Whether the data includes the IoT device object at the end of the data list.
    """
    # Use this to scale the utilities respective to each other.
    # We keep the utilities as-is per algorithm and standardize separately.
    # Find the maximum utility
    max_utility = max([u.utility for u in data])

    # Find the minimum utility
    min_utility = min([u.utility for u in data])

    # Scaling utilities
    if not is_iot_device:
        for u in data:
            # check that utilities are non-zero
            if max_utility != 0:
                u.norm_utility = (u.utility - min_utility) / (max_utility - min_utility) * 100

    # check that utilities are non-zero
    else:
        if max_utility != 0:
            # Scale iot device utility
            data[-1].norm_utility = ((data[-1].utility - min_utility) / (max_utility - min_utility) * 100) / len(
                data)


# Define the PDF DF_w^v(x) for the uniform distribution U
def DF_w_v(x, a, b):
    if a <= x <= b:
        return 1 / (b - a)
    else:
        return 0


# Define the integral function to solve for z
def integral_function(z, a, b, c_w):
    # Define the integrand
    def integrand(x):
        return (x - z) * DF_w_v(x, a, b)

    # Compute the integral from z to b
    integral_value, _ = quad(integrand, z, b)

    # The equation to solve for: integral_value - c(w) = 0
    return integral_value - c_w


# Solve for z using fsolve
def solve_for_z(a, b, c_w):
    # Initial guess for z (start with the midpoint of the range)
    z_initial_guess = (a + b) / 2

    # Solve for z using numerical method
    z_solution = fsolve(integral_function, z_initial_guess, args=(a, b, c_w))[0]

    return z_solution
