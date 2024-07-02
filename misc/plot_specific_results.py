import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re

# Function to read the CSV file
def read_csv():
    file_path = input("Enter the path to the CSV file: ").strip()
    return pd.read_csv(file_path)

# Function to get user input from command line
def get_user_input(base_metrics):
    print("Available base metrics:", ", ".join(base_metrics))
    metric_base = input("Enter the base metric you want to plot: ").strip()

    group_by_options = ['Scenario', 'Network', 'Protocol']
    print("Group by options:", ", ".join(group_by_options))
    group_by = input("Enter how you want to group the bars: ").strip()

    plot_by_options = [col for col in group_by_options if col != group_by]
    print("Plot by options:", ", ".join(plot_by_options))
    plot_by = input("Enter how you want to group the bars: ").strip()

    return metric_base, group_by, plot_by

# Function to plot the data
def plot_data(df, metric_base, group_by, plot_by):
    metric_avg = f"Avg {metric_base}"
    metric_std = f"Std {metric_base}"

    # Function to format labels
    def format_label(label):
        if label.lower() == 'ble':
            return 'BLE'
        elif label.lower() == 'zigbee':
            return 'Zigbee'
        elif label.lower() == 'lora':
            return 'LoRa'
        else:
            return label.capitalize()  # Capitalize first letter if not a specific case

    # Define hatch patterns for different groups
    hatch_patterns = ['/', 'x', '.', '\\', 'o', '+', '*']

    other_categories = [col for col in ['Scenario', 'Network', 'Protocol'] if col != group_by and col != plot_by]

    groups = df[group_by].unique()
    category1 = df[plot_by].unique()
    category2 = df[other_categories[0]].unique()

    figures = []  # List to hold figures

    # Create separate figures for each unique combination of the other categories
    for cat2_idx, cat2 in enumerate(category2):
        means = []
        stds = []

        for group_idx, group in enumerate(groups):
            group_means = []
            group_stds = []

            for cat1_idx, cat1 in enumerate(category1):
                filtered_df = df[(df[group_by] == group) & (df[plot_by] == cat1) & (df[other_categories[0]] == cat2)]

                if not filtered_df.empty:
                    avg = filtered_df[metric_avg].values[0]
                    std = filtered_df[metric_std].values[0]
                else:
                    avg = std = 0  # handle cases where the filtered_df is empty

                group_means.append(avg)
                group_stds.append(std)

            means.append(group_means)
            stds.append(group_stds)

        ind = np.arange(len(category1))
        width = 0.35

        fig, ax = plt.subplots(figsize=(10, 6))
        figures.append(fig)  # Add figure to the list

        rects_list = []
        for group_idx, group in enumerate(groups):
            formatted_group = format_label(group)
            hatch_pattern = hatch_patterns[group_idx % len(hatch_patterns)]  # Cycle through hatch patterns
            rects = ax.bar(ind - width/2 + group_idx*(width/len(groups)), means[group_idx], width/len(groups),
                           yerr=stds[group_idx], label=formatted_group, hatch=hatch_pattern)
            rects_list.append(rects)

        ax.set_ylabel('Average ' + metric_base, fontsize=18)
        ax.tick_params(axis='y', which='major', labelsize=16)
        ax.set_xticks(ind)
        ax.set_xticklabels([format_label(cat) for cat in category1], fontsize=18)
        ax.legend(bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left",
                   mode="expand", borderaxespad=0, ncol=3, fontsize=18)

        # Add gridlines
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)

        title = f'{format_label(cat2)}'
        # Set the window title
        fig.canvas.manager.set_window_title(title)

        def autolabel(rects, xpos='center'):
            ha = {'center': 'center', 'right': 'left', 'left': 'right'}
            offset = {'center': 0, 'right': 1, 'left': -1}

            for rect in rects:
                height = rect.get_height()
                ax.annotate(f'{height:.2f}',
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(offset[xpos]*3, 3),
                            textcoords="offset points",
                            ha=ha[xpos], va='bottom', fontsize=11)

        for rects in rects_list:
            autolabel(rects)

        fig.tight_layout()

    # Show all figures at once
    plt.show()

# Main script
df = read_csv()

# Extract base metrics
pattern = re.compile(r'^(Avg|Max|Min|Std) (.+)$')
base_metrics = set()
for col in df.columns:
    match = pattern.match(col)
    if match:
        base_metrics.add(match.group(2))

metric_base, group_by, plot_by = get_user_input(base_metrics)

plot_data(df, metric_base, group_by, plot_by)
