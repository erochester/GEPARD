import numpy as np
import shutil
import os
import csv
import random
import math

def calc_utility(time, energy, weights):
    # Calculate the utility of the device
    # Use multi-attribute utility function that has been logarithmically transformed
    k = 100 #  scaling factor

    # utility = k * (weights[0] * np.log(1+time)/np.log(1+energy))
    utility = k * np.log(1 + time) / np.log(1 + energy)

    return utility

def calc_time_remaining(user):
    # Calculate user's time remaining in the environment
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
    if np.sqrt((curr_loc[0] ** 2 + curr_loc[1] ** 2)) >= distance:
        return False
    else:
        return True


def result_file_util(filename):
    # Check if the file exists
    if os.path.isfile(filename):
        # File exists, ask the user what to do
        choice = input(
            f"The file {filename} already exists. "
            f"Do you want to remove it (type 'r') or back it up (type 'b')? ")

        # Remove the file
        if choice.lower() == 'r':
            os.remove(filename)
            print(f"The file {filename} has been removed.")
        # Back up the file
        elif choice.lower() == 'b':
            backup_filename = filename + '.bak'
            shutil.copyfile(filename, backup_filename)
            print(f"The file {filename} has been backed up as {backup_filename}.")
            os.remove(filename)
        # Invalid choice
        else:
            print("Invalid choice.")
            exit(1)


def write_results(filename, rows):
    # Check if the directory exists, if not create it
    directory = os.path.dirname(filename)
    if directory != '' and not os.path.exists(directory):
        create_dir = input(f"The directory {directory} does not exist. Do you want to create it? (y/n): ")
        if create_dir.lower() == 'y':
            os.makedirs(directory)
        else:
            print("The directory does not exist. Please create it and try again.")
            exit(-1)
    # Open a file for writing
    mode = "a" if os.path.exists(filename) else "w"
    with open(filename, mode) as csvfile:
        # Create a CSV writer object
        csvwriter = csv.writer(csvfile)

        # Write the column headers only if the file is newly created
        if mode == "w":
            fields = ["Algorithm", "Network", "Scenario", "Total User Power Consumption (W)",
                      "Total Owner Power Consumption (W)", "Total User Time Spent (s)", "Total Owner Time Spent (s)",
                      "Consent collected from", "Total user number",
                      "Consent Percentage (%)", "Total runtime (min)", "Average User Utility", "Total Owner Utility"]
            csvwriter.writerow(fields)

        # Write the data rows
        csvwriter.writerows(rows)

class Distribution():
    def __init__(self, distribution_type):
        self.distribution_type = distribution_type

    def generate_random_samples(self, rate):
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
