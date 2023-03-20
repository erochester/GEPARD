import numpy as np
import shutil
import os
import csv


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
    # Open a file for writing
    mode = "a" if os.path.exists(filename) else "w"
    with open(filename, mode) as csvfile:
        # Create a CSV writer object
        csvwriter = csv.writer(csvfile)

        # Write the column headers only if the file is newly created
        if mode == "w":
            fields = ["Algorithm", "Network", "Scenario", "Total User Power Consumption (kWh)",
                      "Total Owner Power Consumption (kWh)", "Consent collected from", "Total user number",
                      "Consent Percentage", "Total runtime (min)"]
            csvwriter.writerow(fields)

        # Write the data rows
        csvwriter.writerows(rows)