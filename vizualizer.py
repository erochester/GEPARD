import pandas as pd
import matplotlib.pyplot as plt

# Load the data from the CSV file
df = pd.read_csv('results.csv')

# Get the unique networks and scenarios from the data
networks = df['Network'].unique()
scenarios = df['Scenario'].unique()

# Define the colors and hatch patterns for each network and scenario
network_colors = {network: f'C{i}' for i, network in enumerate(networks)}
network_hatches = {network: '/' for network in networks}
scenario_colors = {scenario: f'C{i+2}' for i, scenario in enumerate(scenarios)}
scenario_hatches = {scenario: '-' for scenario in scenarios}

# Create a bar plot for each network
fig, axs = plt.subplots(ncols=len(networks), figsize=(20, 5), sharey=True)
for i, network in enumerate(networks):
    data = df[df['Network'] == network]
    print(network_colors)
    axs[i].bar(data['Scenario'], data['Consent Percentage'], color=network_colors, hatch=network_hatches, edgecolor='black')
    print(data['Scenario'])
    axs[i].set_xlabel('Scenario')
    axs[i].set_ylabel('Consent Percentage')
    axs[i].set_title(network)
    axs[i].set_ylim([0, 100])
    axs[i].grid(axis='y')

# Add a legend for the network colors and hatch patterns
handles, labels = axs[0].get_legend_handles_labels()
network_handles = [plt.Rectangle((0,0),1,1, color=network_colors[network], hatch=network_hatches[network], edgecolor='black') for network in networks]
handles += network_handles
labels += networks.tolist()
fig.legend(handles, labels, loc='lower center', ncol=len(networks)+1, fancybox=True, shadow=True)

# Create a bar plot for each scenario
fig, axs = plt.subplots(ncols=len(scenarios), figsize=(20, 5), sharey=True)
for i, scenario in enumerate(scenarios):
    data = df[df['Scenario'] == scenario]
    axs[i].bar(data['Network'], data['Consent Percentage'], color=scenario_colors[scenario], hatch=scenario_hatches[scenario], edgecolor='black')
    axs[i].set_xlabel('Network')
    axs[i].set_ylabel('Consent Percentage')
    axs[i].set_title(scenario)
    axs[i].set_ylim([0, 100])
    axs[i].grid(axis='y')

# Add a legend for the scenario colors and hatch patterns
handles, labels = axs[0].get_legend_handles_labels()
scenario_handles = [plt.Rectangle((0,0),1,1, color=scenario_colors[scenario], hatch=scenario_hatches[scenario], edgecolor='black') for scenario in scenarios]
handles += scenario_handles
labels += scenarios.tolist()
fig.legend(handles, labels, loc='lower center', ncol=len(scenarios)+1, fancybox=True, shadow=True)

# Show the plots
plt.show()
