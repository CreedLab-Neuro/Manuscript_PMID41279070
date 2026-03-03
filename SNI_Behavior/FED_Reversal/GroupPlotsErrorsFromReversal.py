# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 14:20:17 2025

@author: meagh
"""

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
#%%
# Define the directory containing your CSV files
directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral\SHAM'
#%%

# Get a list of all CSV files in the directory
csv_files = glob.glob(os.path.join(directory, '*.csv'))

# Create a figure for plotting the results
n_files = len(csv_files)
n_cols = 3  # Number of columns for subplots
n_rows = (n_files + n_cols) // n_cols  # Add one row for the final panel
fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows), sharex=True, sharey=True)
axes = axes.flatten()  # Flatten axes to make indexing easier

# Function to calculate mean and SEM
def calculate_mean_and_sem(plot_data, num_reversals_to_average):
    aligned_data = pd.DataFrame()
    for subset in plot_data[:num_reversals_to_average]:
        aligned_data = pd.concat([aligned_data, subset.set_index('Pellets_From_Reversal')['Errors']], axis=1)

    mean_errors = aligned_data.mean(axis=1, skipna=True)
    sem_errors = aligned_data.sem(axis=1, skipna=True)
    return mean_errors, sem_errors

# Initialize storage for aggregating all plots
all_mean_errors = []
all_sem_errors = []
all_data = []

# Loop through each CSV file
for i, csv_file in enumerate(csv_files):
    # Load the data from the current CSV file
    data = pd.read_csv(csv_file)
    print(csv_file)

    # Initialize the list to store pellet counts at reversals
    reversals = []

    # Identify reversals
    for j in range(1, len(data)):
        if data.loc[j, 'Active_Poke'] != data.loc[j - 1, 'Active_Poke']:
            reversals.append(data.loc[j, 'Pellet_Count'])
    print(" ", len(reversals))

    # Prepare the error data for plotting
    errors = []
    current_errors = []
    accuracy = 0
    pellet_number = 0

    for index, row in data.iterrows():
        event = row['Event']
        active_poke = row['Active_Poke']

        if event == 'Pellet':
            pellet_number += 1
            errors.append((pellet_number, len(current_errors)))
            current_errors = []
        elif event in ['Left', 'Right']:
            if event != active_poke:
                current_errors.append(1)

    # Convert errors to a DataFrame
    error_data = pd.DataFrame(errors, columns=['Pellet_Number', 'Errors'])

    # Prepare data for plotting
    plot_data = []
    for reversal in reversals:
        start_pellet = reversal - 10
        end_pellet = reversal + 10
        subset = error_data[(error_data['Pellet_Number'] >= start_pellet) &
                            (error_data['Pellet_Number'] <= end_pellet)].copy()
        subset['Pellets_From_Reversal'] = subset['Pellet_Number'] - reversal
        plot_data.append(subset)

    # Calculate the mean and SEM
    num_reversals_to_average = 6 #len(plot_data) specify this number or plot ALL the reversals
    mean_errors, sem_errors = calculate_mean_and_sem(plot_data, num_reversals_to_average)

    # Store the mean and SEM for the final panel
    all_mean_errors.append(mean_errors)
    all_sem_errors.append(sem_errors)

    # Store all data for averaging later
    all_data.append(pd.concat(plot_data, axis=0))

    # Plotting in the corresponding subplot
    ax = axes[i]

    # Determine color scheme based on filename
    if "MSHAM" in csv_file or "MSNI" in csv_file:
        colors = cm.magma(np.linspace(0, 1, len(plot_data)))
    elif "FSHAM" in csv_file or "FSNI" in csv_file:
        colors = cm.viridis(np.linspace(0, 1, len(plot_data)))

    for subset, color in zip(plot_data, colors):
        ax.plot(subset['Pellets_From_Reversal'], subset['Errors'], marker='o', linestyle='-', alpha=0.5, color=color)

    # Overlay mean and SEM
    ax.plot(mean_errors.index, mean_errors, color='black', linewidth=3, label='Mean Errors')
    ax.axvline(0, color='black', linestyle='--', label='Reversal Point')
    ax.set_xlabel('Pellets from Reversal')
    ax.set_ylabel('Number of Errors')
    ax.set_title(f'Errors Before and After Reversals\n{os.path.basename(csv_file)}')
    ax.grid()

# Calculate the overall mean and SEM for the final panel
overall_mean_errors = pd.concat(all_mean_errors, axis=1).mean(axis=1, skipna=True)
overall_sem_errors = pd.concat(all_mean_errors, axis=1).sem(axis=1, skipna=True)

# Drop NaN values to ensure valid data for plotting
overall_mean_errors = overall_mean_errors.dropna()
overall_sem_errors = overall_sem_errors.loc[overall_mean_errors.index]

# Final panel for the overall mean and SEM
ax = axes[-1]  # Use the last axis
colors = cm.Blues(np.linspace(0.4, 1, len(all_data)))

for i, subset in enumerate(all_data):
    subset_mean = subset.groupby('Pellets_From_Reversal')['Errors'].mean()

    # Set line style based on filename
    if any(keyword in csv_files[i] for keyword in ["FSHAM", "FSNI"]):
        linestyle = '--'  # Dashed
    else:
        linestyle = '-'  # Solid

    ax.plot(subset_mean.index, subset_mean, linestyle=linestyle, alpha=0.4, color=colors[i])

# Overlay overall mean and SEM
ax.plot(overall_mean_errors.index, overall_mean_errors, color='blue', linewidth=3, label='Mean Errors (All Files)')
ax.axvline(0, color='black', linestyle='--', label='Reversal Point')
ax.set_xlabel('Pellets from Reversal')
ax.set_ylabel('Number of Errors')
ax.set_title('Overall Mean Errors Across All Files')
ax.legend()
ax.grid()

# Show the figure. Females are dashed lines, males are solid.F
plt.tight_layout()
plt.savefig('ErrorsFromReversalSHAM_Interim5trials.svg')
plt.show()
