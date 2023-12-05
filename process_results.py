import csv
import numpy as np
import re

import pandas as pd
import matplotlib.pyplot as plt


class ResultProcessor:
    def process_results(self):
        filename = "./results/results.csv"

        # Define dictionaries to store the data
        algorithms = {}
        networks = {}
        scenarios = {}

        with (open(filename, "r") as csvfile):
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Extract the fields from the row
                algorithm = row["Algorithm"]
                network = row["Network"]
                scenario = row["Scenario"]
                user_current = float(row["Total User Current Consumption (W)"])
                owner_current = float(row["Total Owner Current Consumption (W)"])
                user_time = float(row["Total User Time Spent (s)"])
                owner_time = float(row["Total Owner Time Spent (s)"])
                consent = float(row["Consent Percentage (%)"])
                runtime = float(row["Total runtime (min)"])
                user_utility = float(row["Average User Utility"])
                owner_utility = float(row["Total Owner Utility"])

                # Update the dictionaries
                if algorithm not in algorithms:
                    algorithms[algorithm] = {}
                if network not in networks:
                    networks[network] = {}
                if scenario not in scenarios:
                    scenarios[scenario] = {}

                if network not in algorithms[algorithm]:
                    algorithms[algorithm][network] = {}
                if scenario not in algorithms[algorithm][network]:
                    algorithms[algorithm][network][scenario] = []

                algorithms[algorithm][network][scenario].append({
                    "user_current": user_current,
                    "owner_current": owner_current,
                    "user_time": user_time,
                    "owner_time": owner_time,
                    "consent": consent,
                    "runtime": runtime,
                    "user utility": user_utility,
                    "owner utility": owner_utility
                })

        with open('./results/statistics.csv', mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(
                ['Algorithm', 'Network', 'Scenario', 'Avg User Power', 'Min User Current', 'Max User Current',
                 'Std User Current',
                 'Avg Owner Current', 'Min Owner Current', 'Max Owner Current', 'Std Owner Current',
                 'Avg User Time', 'Min User Time', 'Max User Time', 'Std User Time',
                 'Avg Owner Time', 'Min Owner Time', 'Max Owner Time', 'Std Owner Time',
                 'Avg Consent', 'Min Consent', 'Max Consent', 'Std Consent',
                 'Avg Runtime', 'Min Runtime', 'Max Runtime', 'Std Runtime', 'Avg User Utility',
                 'Min User Utility', 'Max User Utility', 'Std User Utility', 'Avg Owner Utility',
                 'Min Owner Utility', 'Max Owner Utility', 'Std Owner Utility'
                 ])

            # Find the combination with the lowest power consumption, highest user consent, and least time taken
            min_power = float("inf")
            best_algorithm = ""
            best_network = ""
            best_scenario = ""

            max_consent_test = 0
            best_algorithm_consent = ""
            best_network_consent = ""
            best_scenario_consent = ""

            min_time = float("inf")
            best_algorithm_time = ""
            best_network_time = ""
            best_scenario_time = ""

            max_user_utility_test = 0
            best_algorithm_utility = ""
            best_network_utility = ""
            best_scenario_utility = ""

            # Calculate the statistics for each combination of algorithm, network, and scenario
            for algorithm, algorithm_data in algorithms.items():
                for network, network_data in algorithm_data.items():
                    for scenario, scenario_data in network_data.items():
                        user_current = [data["user_current"] for data in scenario_data]
                        owner_current = [data["owner_current"] for data in scenario_data]
                        user_time = [data["user_time"] for data in scenario_data]
                        owner_time = [data["owner_time"] for data in scenario_data]
                        consents = [data["consent"] for data in scenario_data]
                        runtimes = [data["runtime"] for data in scenario_data]
                        user_utility = [data["user utility"] for data in scenario_data]
                        owner_utility = [data["owner utility"] for data in scenario_data]

                        # Calculate the statistics
                        avg_user_current = round(np.mean(user_current), 2)
                        avg_owner_current = round(np.mean(owner_current), 2)
                        avg_user_time = round(np.mean(user_time), 2)
                        avg_owner_time = round(np.mean(owner_time), 2)
                        avg_consent = round(np.mean(consents), 2)
                        avg_runtime = round(np.mean(runtimes), 2)
                        avg_user_utility = round(np.mean(user_utility), 2)
                        avg_owner_utility = round(np.mean(owner_utility), 2)

                        if min(avg_user_current, avg_owner_current) < min_power:
                            min_power = min(avg_user_current, avg_owner_current)
                            best_algorithm = algorithm
                            best_network = network
                            best_scenario = scenario

                        if avg_consent > max_consent_test:
                            max_consent_test = avg_consent
                            best_algorithm_consent = algorithm
                            best_network_consent = network
                            best_scenario_consent = scenario

                        if min(avg_user_time, avg_owner_time) < min_time:
                            min_time = min(avg_user_time, avg_owner_time)
                            best_algorithm_time = algorithm
                            best_network_time = network
                            best_scenario_time = scenario

                        if avg_user_utility > max_user_utility_test:
                            max_user_utility_test = avg_user_utility
                            best_algorithm_utility = algorithm
                            best_network_utility = network
                            best_scenario_utility = scenario

                        min_user_current = round(np.min(user_current), 2)
                        min_owner_current = round(np.min(owner_current), 2)
                        min_user_time = round(np.min(user_time), 2)
                        min_owner_time = round(np.min(owner_time), 2)
                        min_consent = round(np.min(consents), 2)
                        min_runtime = round(np.min(runtimes), 2)
                        min_user_utility = round(np.min(user_utility), 2)
                        min_owner_utility = round(np.min(owner_utility), 2)

                        max_user_current = round(np.max(user_current), 2)
                        max_owner_current = round(np.max(owner_current), 2)
                        max_user_time = round(np.max(user_time), 2)
                        max_owner_time = round(np.max(owner_time), 2)
                        max_consent = round(np.max(consents), 2)
                        max_runtime = round(np.max(runtimes), 2)
                        max_user_utility = round(np.max(user_utility), 2)
                        max_owner_utility = round(np.max(owner_utility), 2)

                        std_user_current = round(np.std(user_current), 2)
                        std_owner_current = round(np.std(owner_current), 2)
                        std_user_time = round(np.std(user_time), 2)
                        std_owner_time = round(np.std(owner_time), 2)
                        std_consent = round(np.std(consents), 2)
                        std_runtime = round(np.std(runtimes), 2)
                        std_user_utility = round(np.std(user_utility), 2)
                        std_owner_utility = round(np.std(owner_utility), 2)

                        # Write the data to the file
                        writer.writerow(
                            [algorithm, network, scenario, avg_user_current, min_user_current, max_user_current,
                             std_user_current,
                             avg_owner_current, min_owner_current, max_owner_current, std_owner_current, avg_user_time,
                             min_user_time, max_user_time, std_user_time, avg_owner_time, min_owner_time,
                             max_owner_time,
                             std_owner_time,
                             avg_consent, min_consent,
                             max_consent, std_consent, avg_runtime, min_runtime, max_runtime, std_runtime,
                             avg_user_utility, min_user_utility, max_user_utility, std_user_utility,
                             avg_owner_utility, min_owner_utility, max_owner_utility, std_owner_utility])

            # Open the file for writing
            with open('./results/top_performers.txt', 'w') as f:
                # Write the combination with the least power consumption to the file
                f.write("The combination with the least current consumption is:\n")
                f.write(f"Algorithm: {best_algorithm}\n")
                f.write(f"Network: {best_network}\n")
                f.write(f"Scenario: {best_scenario}\n")
                f.write(f"Current Consumption: {min_power:.2f}\n")
                f.write("\n")

                # Write the combination with the highest user consent to the file
                f.write("The combination with the highest user consent is:\n")
                f.write(f"Algorithm: {best_algorithm_consent}\n")
                f.write(f"Network: {best_network_consent}\n")
                f.write(f"Scenario: {best_scenario_consent}\n")
                f.write(f"User Consent: {max_consent_test:.2f}\n")
                f.write("\n")

                # Write the combination with the least time taken to the file
                f.write("The combination with the least time taken is:\n")
                f.write(f"Algorithm: {best_algorithm_time}\n")
                f.write(f"Network: {best_network_time}\n")
                f.write(f"Scenario: {best_scenario_time}\n")
                f.write(f"Time Taken: {min_time:.2f}\n")
                f.write("\n")

                # Write the combination with the highest user utility to the file
                f.write("The combination with the highest user utility is:\n")
                f.write(f"Algorithm: {best_algorithm_utility}\n")
                f.write(f"Network: {best_network_utility}\n")
                f.write(f"Scenario: {best_scenario_utility}\n")
                f.write(f"User Utility: {max_user_utility_test:.2f}\n")
                f.write("\n")

            # Close the file
            f.close()


    def plot_results(self):
        # FIXME doesnt work for now
        # read data from CSV file
        df = pd.read_csv('./results/results.csv')

        # Find the number of unique scenarios in the DataFrame
        z = df['Scenario'].nunique()

        # Group data by algorithm, network, and scenario
        groups = df.groupby(['Algorithm', 'Network', 'Scenario'])

        for j in range(3, len(df.columns)):
            # Create subplots with 4 columns and as many rows as needed
            # fig, axes = plt.subplots(nrows=len(groups) // 4, ncols=4, figsize=(16, 16))
            fig, axes = plt.subplots(nrows=len(groups) // z + (len(groups) % z > 0), ncols=z, figsize=(16, 16))
            for i, (group, data) in enumerate(groups):
                # ax = axes[i // 4, i % 4]  # Get the corresponding subplot axis
                ax = axes[i // z, i % z]  # Get the corresponding subplot axis
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

