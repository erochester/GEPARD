import pandas as pd
import matplotlib.pyplot as plt
import decimal

# Load the data from csv file
df = pd.read_csv('results.csv')

# Get the unique network types
networks = df['Network'].unique()

# Get the unique scenarios
scenarios = df['Scenario'].unique()

# Get the unique algorithms
algorithms = df['Algorithm'].unique()

hatch_patterns = ['/', '|', '-', '+', 'x', 'o', 'O', '.', '*']

algorithm_colors = [f'C{i}' for i, algorithm in enumerate(algorithms)]
algorithm_hatches = [hatch_patterns[i % len(hatch_patterns)] for i, algorithm in enumerate(algorithms)]

# Loop through the network types
for network in networks:
    # Create a figure and subplot for each network
    fig, axs = plt.subplots(ncols=len(scenarios), figsize=(20, 5), sharey=True)

    # Loop through the scenarios
    for i, scenario in enumerate(scenarios):
        # Filter the data for the current network and scenario
        data = df[(df['Network'] == network) & (df['Scenario'] == scenario)]

        # Create a bar plot for the current network and scenario
        axs[i].bar(data['Algorithm'], data['Total User Power Consumption (kWh)'], color=algorithm_colors,
                   hatch=algorithm_hatches)
        axs[i].set_xlabel('Algorithm')
        axs[i].set_ylabel('Power Consumption (kWh)')
        axs[i].set_title(f'{network} - {scenario}')
        axs[i].grid(axis='y')
        for j, v in enumerate(data['Total User Power Consumption (kWh)']):
            d = decimal.Decimal(str(v))
            # Find the number of decimal places
            places = d.as_tuple().exponent * -1
            axs[i].text(j, v + 1/(10**(places+1)), f"{v:.2f} kWh", ha='center', va='bottom', fontweight='bold')

    # Show the plot for the current network
    plt.show()
