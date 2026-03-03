# -*- coding: utf-8 -*-
"""
Created on Sat Jan  4 15:50:02 2025

@author: meagh
"""

import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#%%
directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral\SHAM'
directory2 = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral\SHAM'
#%%
fig, axes = plt.subplots(2, 2, figsize=(5, 15), sharex=True, sharey=True)
axes = axes.flatten()

#%%
###THIS TOP CODE PLOTS THE MEAN +/- SEM OF THE DATA
# Get a list of all CSV files in the directory
csv_files = glob.glob(os.path.join(directory, '*.csv'))

# Create a figure for plotting
fig, ax = plt.subplots(figsize=(10, 6))

# Initialize storage for all reversal data
all_reversal_data = []  # Store total errors for each file
max_reversals = 10      # Maximum number of reversals to consider

# Loop through each CSV file
for file_name in csv_files:
    # Load the data from the current CSV file
    data = pd.read_csv(file_name)
    print(f"Processing file: {file_name}")

    # Identify reversals
    reversals = []
    for j in range(1, len(data)):
        if data.loc[j, 'Active_Poke'] != data.loc[j - 1, 'Active_Poke']:
            reversals.append(data.loc[j, 'Pellet_Count'])

    # Prepare to count errors for the first 5 pellets after each reversal
    reversal_data = []
    for reversal_idx, reversal_pellet in enumerate(reversals[:max_reversals]):
        subset = data[(data['Pellet_Count'] > reversal_pellet) & 
                      (data['Pellet_Count'] <= reversal_pellet + 5)]

        # Count total errors (non-active pokes) for this reversal
        total_errors = subset.apply(
            lambda row: 1 if row['Event'] in ['Left', 'Right'] and row['Event'] != row['Active_Poke'] else 0, axis=1
        ).sum()
        reversal_data.append((reversal_idx + 1, total_errors))

    # Store the reversal data
    all_reversal_data.append((file_name, reversal_data))

    # Extract reversal numbers and errors
    reversal_numbers, total_errors = zip(*reversal_data)

    # Determine color based on the file name
    if "MSHAM" in file_name or "MSNI" in file_name:
        colormap = plt.cm.magma
        linestyle = '-'  # Solid line
    elif "FSHAM" in file_name or "FSNI" in file_name:
        colormap = plt.cm.viridis
        linestyle = '--'  # Dashed line
    else:
        colormap = plt.cm.tab20
        linestyle = '-'  # Default solid line

    # Normalize colors for the plot
    colors = colormap(np.linspace(0, 1, max_reversals))

    # Plot total errors for each reversal
    for i, (reversal, error) in enumerate(reversal_data):
        ax.plot(reversal, error, marker='o', color=colors[i], linestyle=linestyle, alpha=0.6)

# Compute overall mean and SEM across all files
# Compute overall mean and SEM across all files
all_reversals = np.array([
    np.pad(
        [float(error) for _, error in reversal_data],  # Ensure errors are floats
        (0, max_reversals - len(reversal_data)), 
        constant_values=np.nan
    )
    for _, reversal_data in all_reversal_data
])

# Calculate mean and SEM across files
mean_errors = np.nanmean(all_reversals, axis=0)
sem_errors = np.nanstd(all_reversals, axis=0) / np.sqrt(np.sum(~np.isnan(all_reversals), axis=0))

# Overlay mean line with SEM
reversal_numbers = np.arange(1, max_reversals + 1)
ax.plot(reversal_numbers, mean_errors, color='black', linewidth=3, label='Mean (All Files)')
ax.fill_between(
    reversal_numbers,
    mean_errors - sem_errors,
    mean_errors + sem_errors,
    color='black',
    alpha=0.2,
    label='SEM'
)

# Final plot settings
ax.set_xlabel('Reversal Number')
ax.set_ylabel('Total Errors (First 5 Pellets After Reversal)')
ax.set_title('Total Errors per Reversal Across Files')
ax.legend()
ax.grid(True)

# Show the plot
plt.show()

#%% THIS CODE PLOTS THE INDIVIDUALS IN THE DIRECTORY
# Get a list of all CSV files in the directory
csv_files = glob.glob(os.path.join(directory, '*.csv'))

# Initialize storage for the aggregated data
all_reversal_data = []

# Loop through each CSV file
for csv_file in csv_files:
    # Load the data from the current CSV file
    data = pd.read_csv(csv_file)
    print(f"Processing file: {csv_file}")

    # Initialize the list to store pellet counts at reversals
    reversals = []

    # Identify reversals
    for j in range(1, len(data)):
        if data.loc[j, 'Active_Poke'] != data.loc[j - 1, 'Active_Poke']:
            reversals.append(data.loc[j, 'Pellet_Count'])

    # Prepare the error data
    errors = []
    current_errors = []
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

    # Aggregate total errors for the first 5 pellets after each reversal
    reversal_data = []
    for reversal_index, reversal in enumerate(reversals[:8], start=1):  # Limit to first 10 reversals
        subset = error_data[(error_data['Pellet_Number'] > reversal) &
                            (error_data['Pellet_Number'] <= reversal + 5)]
        total_errors = subset['Errors'].sum()
        reversal_data.append((reversal_index, total_errors))

    # Store the data for this file
    all_reversal_data.append((os.path.basename(csv_file), reversal_data))

# Plot the data
fig, ax = plt.subplots(figsize=(10, 6))

# Define colors for plotting based on filename
color_map = {
    "MSHAM": "magma",
    "MSNI": "magma",
    "FSHAM": "viridis",
    "FSNI": "viridis",
}



for file_name, reversal_data in all_reversal_data:
    # Determine the colormap based on the filename
    if "MSHAM" in file_name or "MSNI" in file_name:
        colormap = plt.cm.magma
    elif "FSHAM" in file_name or "FSNI" in file_name:
        colormap = plt.cm.viridis
    else:
        raise ValueError(f"Unknown filename pattern in {file_name}")


    # Extract reversal numbers and total errors
    reversal_numbers, total_errors = zip(*reversal_data)

    # Plot the data
    ax.plot(reversal_numbers, total_errors, marker='o', linestyle='-',
            label=file_name, color=colormap(0.6))

# Customize the plot
ax.set_xlabel('Reversal Number')
ax.set_ylabel('Total Errors (First 5 Pellets After Reversal)')
ax.set_title('Total Errors by Reversal Number')
ax.legend(title="Files", bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid()

plt.tight_layout()
plt.show()