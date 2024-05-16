import csv
import numpy as np
import math

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm


class ResultProcessor:
    """
    Result processor class.
    """

    def process_results(self):
        """
        Processes the results stored in "./results/results.csv" to generate statistics and other insights
        and saves them in './results/top_performers.txt' for top performers and
        './results/statistics.csv' for general statistics.
        """
        filename = "./results/results.csv"

        # Define dictionaries to store the data
        protocols = {}
        networks = {}
        scenarios = {}

        with (open(filename, "r") as csvfile):
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Extract the fields from the row
                protocol = row["Protocol"]
                network = row["Network"]
                scenario = row["Scenario"]
                user_power = float(row["Total User Power Consumption (W)"])
                owner_power = float(row["Total Owner Power Consumption (W)"])
                user_time = float(row["Total User Time Spent (s)"])
                owner_time = float(row["Total Owner Time Spent (s)"])
                consent = float(row["Consent Percentage (%)"])
                runtime = float(row["Total runtime (min)"])
                user_utility = float(row["Average User Utility"])
                owner_utility = float(row["Total Owner Utility"])

                # Update the dictionaries
                if protocol not in protocols:
                    protocols[protocol] = {}
                if network not in networks:
                    networks[network] = {}
                if scenario not in scenarios:
                    scenarios[scenario] = {}

                if network not in protocols[protocol]:
                    protocols[protocol][network] = {}
                if scenario not in protocols[protocol][network]:
                    protocols[protocol][network][scenario] = []

                protocols[protocol][network][scenario].append({
                    "user_power": user_power,
                    "owner_power": owner_power,
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
                ['Protocol', 'Network', 'Scenario', 'Avg User Power', 'Min User Power', 'Max User Power',
                 'Std User Power',
                 'Avg Owner Power', 'Min Owner Power', 'Max Owner Power', 'Std Owner Power',
                 'Avg User Time', 'Min User Time', 'Max User Time', 'Std User Time',
                 'Avg Owner Time', 'Min Owner Time', 'Max Owner Time', 'Std Owner Time',
                 'Avg Consent', 'Min Consent', 'Max Consent', 'Std Consent',
                 'Avg Runtime', 'Min Runtime', 'Max Runtime', 'Std Runtime', 'Avg User Utility',
                 'Min User Utility', 'Max User Utility', 'Std User Utility', 'Avg Owner Utility',
                 'Min Owner Utility', 'Max Owner Utility', 'Std Owner Utility'
                 ])

            # Find the combination with the lowest power consumption, highest user consent, and least time taken
            min_power = float("inf")
            best_protocol = ""
            best_network = ""
            best_scenario = ""

            max_consent_test = 0
            best_protocol_consent = ""
            best_network_consent = ""
            best_scenario_consent = ""

            min_time = float("inf")
            best_protocol_time = ""
            best_network_time = ""
            best_scenario_time = ""

            max_user_utility_test = 0
            best_protocol_utility = ""
            best_network_utility = ""
            best_scenario_utility = ""

            # Calculate the statistics for each combination of protocol, network, and scenario
            for protocol, protocol_data in protocols.items():
                for network, network_data in protocol_data.items():
                    for scenario, scenario_data in network_data.items():
                        user_power = [data["user_power"] for data in scenario_data]
                        owner_power = [data["owner_power"] for data in scenario_data]
                        user_time = [data["user_time"] for data in scenario_data]
                        owner_time = [data["owner_time"] for data in scenario_data]
                        consents = [data["consent"] for data in scenario_data]
                        runtimes = [data["runtime"] for data in scenario_data]
                        user_utility = [data["user utility"] for data in scenario_data]
                        owner_utility = [data["owner utility"] for data in scenario_data]

                        # Calculate the statistics
                        avg_user_current = round(np.mean(user_power), 2)
                        avg_owner_current = round(np.mean(owner_power), 2)
                        avg_user_time = round(np.mean(user_time), 2)
                        avg_owner_time = round(np.mean(owner_time), 2)
                        avg_consent = round(np.mean(consents), 2)
                        avg_runtime = round(np.mean(runtimes), 2)
                        avg_user_utility = round(np.mean(user_utility), 2)
                        avg_owner_utility = round(np.mean(owner_utility), 2)

                        if min(avg_user_current, avg_owner_current) < min_power:
                            min_power = min(avg_user_current, avg_owner_current)
                            best_protocol = protocol
                            best_network = network
                            best_scenario = scenario

                        if avg_consent > max_consent_test:
                            max_consent_test = avg_consent
                            best_protocol_consent = protocol
                            best_network_consent = network
                            best_scenario_consent = scenario

                        if min(avg_user_time, avg_owner_time) < min_time:
                            min_time = min(avg_user_time, avg_owner_time)
                            best_protocol_time = protocol
                            best_network_time = network
                            best_scenario_time = scenario

                        if avg_user_utility > max_user_utility_test:
                            max_user_utility_test = avg_user_utility
                            best_protocol_utility = protocol
                            best_network_utility = network
                            best_scenario_utility = scenario

                        min_user_current = round(np.min(user_power), 2)
                        min_owner_current = round(np.min(owner_power), 2)
                        min_user_time = round(np.min(user_time), 2)
                        min_owner_time = round(np.min(owner_time), 2)
                        min_consent = round(np.min(consents), 2)
                        min_runtime = round(np.min(runtimes), 2)
                        min_user_utility = round(np.min(user_utility), 2)
                        min_owner_utility = round(np.min(owner_utility), 2)

                        max_user_current = round(np.max(user_power), 2)
                        max_owner_current = round(np.max(owner_power), 2)
                        max_user_time = round(np.max(user_time), 2)
                        max_owner_time = round(np.max(owner_time), 2)
                        max_consent = round(np.max(consents), 2)
                        max_runtime = round(np.max(runtimes), 2)
                        max_user_utility = round(np.max(user_utility), 2)
                        max_owner_utility = round(np.max(owner_utility), 2)

                        std_user_current = round(np.std(user_power), 2)
                        std_owner_current = round(np.std(owner_power), 2)
                        std_user_time = round(np.std(user_time), 2)
                        std_owner_time = round(np.std(owner_time), 2)
                        std_consent = round(np.std(consents), 2)
                        std_runtime = round(np.std(runtimes), 2)
                        std_user_utility = round(np.std(user_utility), 2)
                        std_owner_utility = round(np.std(owner_utility), 2)

                        # Write the data to the file
                        writer.writerow(
                            [protocol, network, scenario, avg_user_current, min_user_current, max_user_current,
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
                f.write("The combination with the least power consumption is:\n")
                f.write(f"Protocol: {best_protocol}\n")
                f.write(f"Network: {best_network}\n")
                f.write(f"Scenario: {best_scenario}\n")
                f.write(f"Power Consumption: {min_power:.2f}\n")
                f.write("\n")

                # Write the combination with the highest user consent to the file
                f.write("The combination with the highest user consent is:\n")
                f.write(f"Protocol: {best_protocol_consent}\n")
                f.write(f"Network: {best_network_consent}\n")
                f.write(f"Scenario: {best_scenario_consent}\n")
                f.write(f"User Consent: {max_consent_test:.2f}\n")
                f.write("\n")

                # Write the combination with the least time taken to the file
                f.write("The combination with the least time taken is:\n")
                f.write(f"Protocol: {best_protocol_time}\n")
                f.write(f"Network: {best_network_time}\n")
                f.write(f"Scenario: {best_scenario_time}\n")
                f.write(f"Time Taken: {min_time:.2f}\n")
                f.write("\n")

                # Write the combination with the highest user utility to the file
                f.write("The combination with the highest user utility is:\n")
                f.write(f"Protocol: {best_protocol_utility}\n")
                f.write(f"Network: {best_network_utility}\n")
                f.write(f"Scenario: {best_scenario_utility}\n")
                f.write(f"User Utility: {max_user_utility_test:.2f}\n")
                f.write("\n")

            # Close the file
            f.close()

    def plot_results(self):
        """
        Reads data from './results/results.csv' and plots it on a grid of plots.
        """
        # Read data from CSV file
        df = pd.read_csv('./results/results.csv')

        # Group data by Protocol, Network, and Scenario
        groups = df.groupby(['Protocol', 'Network', 'Scenario'])

        # Define the metrics you want to plot
        metrics = ['Total User Power Consumption (W)', 'Total Owner Power Consumption (W)', 'Total User Time Spent (s)',
                   'Total Owner Time Spent (s)', 'Consent Percentage (%)', 'Average User Utility',
                   'Total Owner Utility']

        # Get the number of unique protocols
        num_protocols = len(df['Protocol'].unique())

        # Generate a color map with the number of colors equal to the number of unique protocols
        colors = cm.tab10.colors[:num_protocols]

        # Create a dictionary mapping each protocol to a color
        protocol_colors = dict(zip(df['Protocol'].unique(), colors))

        # Iterate over each metric
        for metric in metrics:
            # Determine the number of subplots needed based on the number of groups
            num_groups = len(groups)
            cols = int(math.sqrt(num_groups)) + 1  # Calculate number of columns dynamically
            rows = (num_groups - 1) // cols + 1  # Calculate number of rows

            # Calculate the figure size based on the number of subplots
            fig_width = 5 * cols
            fig_height = 3 * rows

            # Create a new figure for the current metric with dynamically scaled size
            fig = plt.figure(figsize=(fig_width, fig_height))
            fig.suptitle(metric, fontsize=16)  # Set the figure title to the metric

            # Iterate over each group and create a subplot for each combination of scenario-protocol-network
            for i, (group_name, group_data) in enumerate(groups):
                ax = fig.add_subplot(rows, cols, i + 1)
                scenario_data = group_data[metric]
                protocol = group_name[0]  # Get the protocol name
                color = protocol_colors.get(protocol,
                                             'tab:blue')  # Get the color from the color palette, default to blue
                # ax.bar(group_data.index, scenario_data, yerr=scenario_data.std(), capsize=5,
                #        color=color)  # Use index instead of 'Scenario'
                boxprops = dict(color=color, linewidth=2)  # Set color and line width for the boxplot lines
                mediaprops = dict(color='red', linewidth=3)
                ax.boxplot(scenario_data, patch_artist=False, boxprops=boxprops, medianprops=mediaprops)
                ax.set_ylabel(metric)
                ax.set_title(f'{group_name[0]} - {group_name[1]} - {group_name[2]}')  # Set subplot title
                # ax.tick_params(axis='x', rotation=45)  # Rotate x-axis labels
                ax.set_xticks([])  # Remove x-ticks
                ax.grid(True)

            plt.tight_layout(rect=[0, 0.03, 1, 0.95])  # Adjust layout to accommodate the main title
            plt.savefig('./results/'+f'{metric}.png')  # Save plot as PNG file for the current metric with error bars
            # plt.show()
