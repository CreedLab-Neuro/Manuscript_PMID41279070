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
#directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral\SHAM'
directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral\SNI'
#directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\Debug'
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
        aligned_data = pd.concat([aligned_data, subset.set_index('Pellets_From_Reversal')['Accuracy']], axis=1)

    mean_accuracy = aligned_data.mean(axis=1, skipna=True)
    sem_accuracy = aligned_data.sem(axis=1, skipna=True)
    return mean_accuracy, sem_accuracy

# Initialize storage for aggregating all plots
all_mean_accuracy = []
all_sem_accuracy = []
all_data = []

# Loop through each CSV file
for i, csv_file in enumerate(csv_files):
    # Load the data from the current CSV file
    data = pd.read_csv(csv_file)
    print(csv_file)

    # Ensure relevant columns exist
    required_columns = ["Event", "Active_Poke", "Binary_Left_Pokes", "Binary_Right_Pokes", "Binary_Pellets", "Correct_Poke"]
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        print("This file is good!")                         #f"Skipping file {file_path}: Missing columns {missing_columns}")

        # Initialize the list to store pellet counts at reversals
        reversals = []

        # Identify reversals
        for j in range(1, len(data)):
            if data.loc[j, 'Active_Poke'] != data.loc[j - 1, 'Active_Poke']:
                reversals.append(data.loc[j, 'Pellet_Count'])
        print(len(reversals))

        # Prepare the error data for plotting
        errors = []
        current_errors = []
        pellet_accuracy = 0
        accuracy = []
        pellet_number = 0
        
        for index, row in data.iterrows():
            event = row['Event']
            active_poke = row['Active_Poke']

            if event == 'Pellet':
                pellet_number += 1
                errors.append((pellet_number, len(current_errors)))
                pellet_accuracy = 1/(len(current_errors) + 1)
                accuracy.append((pellet_number, pellet_accuracy))
                #print("Pellet Number: ", pellet_number, " Accuracy: ", pellet_accuracy, " Errors:", len(current_errors))
                current_errors = []
                pellet_accuracy = 0
            elif event in ['Left', 'Right']:
                if event != active_poke:
                    current_errors.append(1)
    
    else:    
        print("This is the new code:")
        # Initialize the list to store pellet counts at reversals
        reversals = []

        # Identify reversals
        for j in range(1, len(data)):
            if data.loc[j, 'Active_Poke'] != data.loc[j - 1, 'Active_Poke']:
                reversals.append(data.loc[j, 'Pellet_Count'])
        print(len(reversals))

        # Prepare the error data for plotting
        errors = []
        current_errors = []
        pellet_accuracy = 0
        accuracy = []
        pellet_number = 0

        for index, row in data.iterrows():
            event = row['Event']
            active_poke = row['Active_Poke']
            if event == 'Pellet':
                pellet_number += 1
                errors.append((pellet_number, len(current_errors)))
                pellet_accuracy = 1/(len(current_errors) + 1)
                accuracy.append((pellet_number, pellet_accuracy))
                #print("Pellet Number: ", pellet_number, " Accuracy: ", pellet_accuracy, " Errors:", len(current_errors))
                current_errors = []
                pellet_accuracy = 0
            elif event == 'Poke':
                if row['Correct_Poke'] == 0:
                    current_errors.append(1)
                    
    # Convert errors to a DataFrame
    error_data = pd.DataFrame(errors, columns=['Pellet_Number', 'Errors'])
    accuracy_data = pd.DataFrame(accuracy, columns=['Pellet_Number', 'Accuracy'])
    #print('Error Data: ', error_data)
    #print('Accuracy Data: ', accuracy_data)

    # Prepare data for plotting
    plot_data = []
    for reversal in reversals:
        start_pellet = reversal - 10
        end_pellet = reversal + 10
        subset = accuracy_data[(accuracy_data['Pellet_Number'] >= start_pellet) &
                            (accuracy_data['Pellet_Number'] <= end_pellet)].copy()
        subset['Pellets_From_Reversal'] = subset['Pellet_Number'] - reversal
        plot_data.append(subset)

    # Calculate the mean and SEM
    num_reversals_to_average = 6 #len(plot_data) specify this number or plot ALL the reversals
    mean_accuracy, sem_accuracy = calculate_mean_and_sem(plot_data, num_reversals_to_average)

    # Store the mean and SEM for the final panel
    all_mean_accuracy.append(mean_accuracy)
    all_sem_accuracy.append(sem_accuracy)

    # Store all data for averaging later
    all_data.append(pd.concat(plot_data, axis=0))

    # Plotting in the corresponding subplot
    ax = axes[i]

    # Determine color scheme based on filename
    if "MSHAM" in csv_file:
        colors = cm.Reds(np.linspace(0, 1, len(plot_data)))
    elif "FSHAM" in csv_file:
        colors = cm.Blues(np.linspace(0, 1, len(plot_data)))
    if "MSNI" in csv_file:
        colors = cm.magma(np.linspace(0, 1, len(plot_data)))
    elif "FSNI" in csv_file:
        colors = cm.viridis(np.linspace(0, 1, len(plot_data)))
    for subset, color in zip(plot_data, colors):
        ax.plot(subset['Pellets_From_Reversal'], subset['Accuracy'], marker='o', linestyle='-', alpha=0.5, color=color)
    

    # Overlay mean and SEM
    ax.plot(mean_accuracy.index, mean_accuracy, color='black', linewidth=3, label='Mean Accuracy')
    ax.axvline(0, color='black', linestyle='--', label='Reversal Point')
    ax.set_xlabel('Pellets from Reversal')
    ax.set_ylabel('P(Rewarded Port)')
    ax.set_title(f'Errors Before and After Reversals\n{os.path.basename(csv_file)}')
    ax.grid()
    
# Calculate the overall mean and SEM for the final panel
overall_mean_accuracy = pd.concat(all_mean_accuracy, axis=1).mean(axis=1, skipna=True)
overall_sem_accuracy = pd.concat(all_sem_accuracy, axis=1).sem(axis=1, skipna=True)

# Drop NaN values to ensure valid data for plotting
overall_mean_accuracy = overall_mean_accuracy.dropna()
overall_sem_accuracy = overall_sem_accuracy.loc[overall_mean_accuracy.index]

# Final panel for the overall mean and SEM
ax = axes[-1]  # Use the last axis
colors = cm.Blues(np.linspace(0.4, 1, len(all_data)))

for i, subset in enumerate(all_data):
    subset_mean = subset.groupby('Pellets_From_Reversal')['Accuracy'].mean()

    # Set line style based on filename
    if any(keyword in csv_files[i] for keyword in ["FSHAM", "FSNI"]):
        linestyle = '--'  # Dashed
    else:
        linestyle = '-'  # Solid

    ax.plot(subset_mean.index, subset_mean, linestyle=linestyle, alpha=0.4, color=colors[i])

# Overlay overall mean and SEM
ax.plot(overall_mean_accuracy.index, overall_mean_accuracy, color='blue', linewidth=3, label='Mean Errors (All Files)')
ax.axvline(0, color='black', linestyle='--', label='Reversal Point')
ax.set_xlabel('Pellets from Reversal')
ax.set_ylabel('Number of Errors')
ax.set_title('Overall Mean Errors Across All Files')
ax.legend()
ax.grid()

# Show the figure. Females are dashed lines, males are solid.F
plt.tight_layout()
plt.savefig('SNI_Accuracy.svg')
plt.savefig('SNI_Accuracy.png')
plt.show()
