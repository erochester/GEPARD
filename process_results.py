import csv
import numpy as np
import re

filename = "./results/results.csv"

# # Define dictionaries to store the data
# algorithms = {}
# networks = {}
# scenarios = {}
#
# with open(filename, "r") as csvfile:
#     reader = csv.DictReader(csvfile)
#     for row in reader:
#         # Extract the fields from the row
#         algorithm = row["Algorithm"]
#         network = row["Network"]
#         scenario = row["Scenario"]
#         user_power = float(row["Total User Power Consumption (kWh)"])
#         owner_power = float(row["Total Owner Power Consumption (kWh)"])
#         user_time = float(row["Total User Time Spent (s)"])
#         owner_time = float(row["Total Owner Time Spent (s)"])
#         consent = float(row["Consent Percentage (%)"])
#         runtime = float(row["Total runtime (min)"])
#
#         # Update the dictionaries
#         if algorithm not in algorithms:
#             algorithms[algorithm] = {}
#         if network not in networks:
#             networks[network] = {}
#         if scenario not in scenarios:
#             scenarios[scenario] = {}
#
#         if network not in algorithms[algorithm]:
#             algorithms[algorithm][network] = {}
#         if scenario not in algorithms[algorithm][network]:
#             algorithms[algorithm][network][scenario] = []
#
#         algorithms[algorithm][network][scenario].append({
#             "user_power": user_power,
#             "owner_power": owner_power,
#             "user_time": user_time,
#             "owner_time": owner_time,
#             "consent": consent,
#             "runtime": runtime
#         })
#
# with open('./results/statistics.csv', mode='w', newline='') as file:
#     writer = csv.writer(file)
#     writer.writerow(
#         ['Algorithm', 'Network', 'Scenario', 'Avg User Power', 'Min User Power', 'Max User Power', 'Std User Power',
#          'Avg Owner Power', 'Min Owner Power', 'Max Owner Power', 'Std Owner Power',
#          'Avg User Time', 'Min User Time', 'Max User Time', 'Std User Time',
#          'Avg Owner Time', 'Min Owner Time', 'Max Owner Time', 'Std Owner Time',
#          'Avg Consent', 'Min Consent', 'Max Consent', 'Std Consent',
#          'Avg Runtime', 'Min Runtime', 'Max Runtime', 'Std Runtime'])
#
#     # Calculate the statistics for each combination of algorithm, network, and scenario
#     for algorithm, algorithm_data in algorithms.items():
#         for network, network_data in algorithm_data.items():
#             for scenario, scenario_data in network_data.items():
#                 user_powers = [data["user_power"] for data in scenario_data]
#                 owner_powers = [data["owner_power"] for data in scenario_data]
#                 user_time = [data["user_time"] for data in scenario_data]
#                 owner_time = [data["owner_time"] for data in scenario_data]
#                 consents = [data["consent"] for data in scenario_data]
#                 runtimes = [data["runtime"] for data in scenario_data]
#
#                 # Calculate the statistics
#                 avg_user_power = round(np.mean(user_powers), 2)
#                 avg_owner_power = round(np.mean(owner_powers), 2)
#                 avg_user_time = round(np.mean(user_time), 2)
#                 avg_owner_time = round(np.mean(owner_time), 2)
#                 avg_consent = round(np.mean(consents), 2)
#                 avg_runtime = round(np.mean(runtimes), 2)
#
#                 min_user_power = round(np.min(user_powers), 2)
#                 min_owner_power = round(np.min(owner_powers), 2)
#                 min_user_time = round(np.min(user_time), 2)
#                 min_owner_time = round(np.min(owner_time), 2)
#                 min_consent = round(np.min(consents), 2)
#                 min_runtime = round(np.min(runtimes), 2)
#
#                 max_user_power = round(np.max(user_powers), 2)
#                 max_owner_power = round(np.max(owner_powers), 2)
#                 max_user_time = round(np.max(user_time), 2)
#                 max_owner_time = round(np.max(owner_time), 2)
#                 max_consent = round(np.max(consents), 2)
#                 max_runtime = round(np.max(runtimes), 2)
#
#                 std_user_power = round(np.std(user_powers), 2)
#                 std_owner_power = round(np.std(owner_powers), 2)
#                 std_user_time = round(np.std(user_time), 2)
#                 std_owner_time = round(np.std(owner_time), 2)
#                 std_consent = round(np.std(consents), 2)
#                 std_runtime = round(np.std(runtimes), 2)
#
#                 # Write the data to the file
#                 writer.writerow(
#                     [algorithm, network, scenario, avg_user_power, min_user_power, max_user_power, std_user_power,
#                      avg_owner_power, min_owner_power, max_owner_power, std_owner_power, avg_user_time,
#                      min_user_time, max_user_time, std_user_time, avg_owner_time, min_owner_time, max_owner_time,
#                      std_owner_time,
#                      avg_consent, min_consent,
#                      max_consent, std_consent, avg_runtime, min_runtime, max_runtime, std_runtime])

import pandas as pd
import matplotlib.pyplot as plt

# read data from CSV file
df = pd.read_csv('./results/results.csv')

# Group data by algorithm, network, and scenario
groups = df.groupby(['Algorithm', 'Network', 'Scenario'])

for j in range(3, len(df.columns)):
    # Create subplots with 4 columns and as many rows as needed
    fig, axes = plt.subplots(nrows=len(groups) // 4, ncols=4, figsize=(16, 16))
    for i, (group, data) in enumerate(groups):
        ax = axes[i // 4, i % 4]  # Get the corresponding subplot axis
        ax.set_title(f"{group[0]} - {group[1]} - {group[2]}")
        data.boxplot(column=df.columns[j], ax=ax)  # Plot boxplot in subplot
        ax.set_xlabel("")  # Remove x-axis label
        substring_list = re.findall(r'\((.*?)\)', df.columns[j])
        # Set y-axis label
        if substring_list:
            ylabel = substring_list[0]
            ax.set_ylabel(ylabel)  # y-axis label
        # Add median value to plot
        median = data[df.columns[j]].median()
        # Special case for total user number
        if df.columns[j] == "Total user number":
            ax.text(0.9, median, f"{int(median)}", ha='right', va='center')
        else:
            ax.text(0.9, median, f"{median:.2f}", ha='right', va='center')

    plt.tight_layout()
    plt.subplots_adjust(hspace=0.5)
    plt.savefig("./results/" + df.columns[j] + ".png")

