# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 11:44:27 2025

@author: meagh
"""

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# Set your directory
directory = r'C:\Users\meagh\Downloads\Clean\Clean\SNI'

# Get all CSV files
csv_files = glob.glob(os.path.join(directory, '*.csv'))

# Function to compute mean and SEM across aligned reversal windows
def calculate_mean_and_sem(plot_data, num_reversals_to_average):
    aligned_data = pd.DataFrame()
    for subset in plot_data[:num_reversals_to_average]:
        aligned_data = pd.concat([aligned_data, subset.set_index('Pellets_From_Reversal')['Accuracy']], axis=1)
    return aligned_data.mean(axis=1, skipna=True), aligned_data.sem(axis=1, skipna=True)

# For aggregating data
all_mean_accuracy = []
all_sem_accuracy = []
all_data = []

# Loop through files
for csv_file in csv_files:
    data = pd.read_csv(csv_file)

    # Identify reversal points
    reversals = [
        data.loc[j, 'Pellet_Count']
        for j in range(1, len(data))
        if data.loc[j, 'Active_Poke'] != data.loc[j - 1, 'Active_Poke']
    ]

    # Track errors and accuracy
    pellet_number = 0
    current_errors = []
    errors = []
    accuracy = []

    for _, row in data.iterrows():
        event = row['Event']
        active_poke = row['Active_Poke']

        if event == 'Pellet':
            pellet_number += 1
            pellet_accuracy = 1 / (len(current_errors) + 1)
            accuracy.append((pellet_number, pellet_accuracy))
            current_errors = []
        elif event in ['Left', 'Right']:
            if event != active_poke:
                current_errors.append(1)

    # Prepare DataFrame
    accuracy_data = pd.DataFrame(accuracy, columns=['Pellet_Number', 'Accuracy'])

    # Extract windows around reversals
    plot_data = []
    for reversal in reversals:
        subset = accuracy_data[
            (accuracy_data['Pellet_Number'] >= reversal - 10) &
            (accuracy_data['Pellet_Number'] <= reversal + 15)
        ].copy()
        subset['Pellets_From_Reversal'] = subset['Pellet_Number'] - reversal
        plot_data.append(subset)

    # Compute mean/SEM
    mean_accuracy, sem_accuracy = calculate_mean_and_sem(plot_data, num_reversals_to_average=6)

    all_mean_accuracy.append(mean_accuracy)
    all_sem_accuracy.append(sem_accuracy)
    all_data.append(pd.concat(plot_data, axis=0))

# Compute grand mean and SEM across files
overall_mean_accuracy = pd.concat(all_mean_accuracy, axis=1).mean(axis=1, skipna=True).dropna()
overall_sem_accuracy = pd.concat(all_sem_accuracy, axis=1).sem(axis=1, skipna=True).loc[overall_mean_accuracy.index]

# === FINAL PLOT ===
fig, ax = plt.subplots(figsize=(8, 6))
colors = cm.Blues(np.linspace(0.4, 1, len(all_data)))

for i, subset in enumerate(all_data):
    subset_mean = subset.groupby('Pellets_From_Reversal')['Accuracy'].mean()
    linestyle = '--' if any(k in csv_files[i] for k in ["FSHAM", "FSNI"]) else '-'
    ax.plot(subset_mean.index, subset_mean, linestyle=linestyle, alpha=0.4, color=colors[i])

# Overlay grand mean and SEM
ax.plot(overall_mean_accuracy.index, overall_mean_accuracy, color='blue', linewidth=3, label='Grand Mean')

ax.axvline(0, color='black', linestyle='--', label='Reversal')
ax.set_xlabel('Pellets from Reversal')
ax.set_ylabel('Accuracy')
ax.set_title('Average Accuracy Around Reversals')
ax.legend()
ax.grid()

plt.tight_layout()
#plt.savefig('MyFigure.png')
#plt.savefig('MyFigure.svg')
plt.show()
