# -*- coding: utf-8 -*-
"""
Created on Wed Dec 25 14:14:44 2024

@author: meagh
"""
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
#%%
# Define the directory containing your CSV files
directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\NaiveReversal'
#directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral\UncategorizedJeffFeb'
#directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral\SNI'
#directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral\Naive'
#directory = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral'
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
def calculate_mean_and_sem(plot_data, num_reversals):
    aligned_data = pd.DataFrame()
    for subset in plot_data[:num_reversals]:
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
    pellet_number = 0

    for index, row in data.iterrows():
        event = row['Event']
        active_poke = row['Active_Poke']

        if event == 'Pellet':
            pellet_number += 1
            errors.append((pellet_number, len(current_errors)))
            current_errors = []
        if event == 'Poke':
            if active_poke == 'Left' and row['Binary_Left_Pokes'] == 0:
                current_errors.append(1)
            elif active_poke == 'Right' and row['Binary_Right_Pokes'] == 0:
                current_errors.append(1)
        # elif event in ['Left', 'Right']:
        #     if event != active_poke:
        #         current_errors.append(1)

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
        #print(subset)
        plot_data.append(subset)
            

    # Calculate the mean and SEM
    num_reversals_to_average = 5 #len(plot_data) CHANGE THIS NUMBER TO BE THE NUMBER OF REVERSALS, or the len(plot_data)
    #print(len(plot_data))
    mean_errors, sem_errors = calculate_mean_and_sem(plot_data, num_reversals_to_average)

    # Store the mean and SEM for the final panel
    all_mean_errors.append(mean_errors)
    all_sem_errors.append(sem_errors)

    # Store all data for averaging later
    all_data.append(pd.concat(plot_data, axis=0))

    # Plotting in the corresponding subplot
    ax = axes[i]
    colors = cm.magma(np.linspace(0, 1, len(plot_data)))

    for subset, color in zip(plot_data, colors):
        ax.plot(subset['Pellets_From_Reversal'], subset['Errors'], marker='o', linestyle='-', alpha=0.5, color=color, label=f'Reversal at Pellet {subset.iloc[10]["Pellet_Number"]}')

    # Overlay mean and SEM
    ax.plot(mean_errors.index, mean_errors, color='black', linewidth=3, label='Mean Errors')
    ax.axvline(0, color='black', linestyle='--', label='Reversal Point')
    ax.set_xlabel('Pellets from Reversal')
    ax.set_ylabel('Number of Errors')
    ax.set_title(f'Errors Before and After Reversals\n{os.path.basename(csv_file)}')
    #ax.legend()
    ax.grid()
    
# Calculate the overall mean and SEM for the final panel
overall_mean_errors = pd.concat(all_mean_errors, axis=1).mean(axis=1, skipna=True)
overall_sem_errors = pd.concat(all_mean_errors, axis=1).sem(axis=1, skipna=True)

# Drop NaN values to ensure valid data for plotting
overall_mean_errors = overall_mean_errors.dropna()
overall_sem_errors = overall_sem_errors.loc[overall_mean_errors.index]

print("Overall Mean Errors:")
print(overall_mean_errors)
print("Overall SEM Errors:")
print(overall_sem_errors)

# Final panel for the overall mean and SEM
ax = axes[-1]  # Use the last axis
colors = cm.Blues(np.linspace(0.4, 1, len(all_data)))

for i, subset in enumerate(all_data):
    subset_mean = subset.groupby('Pellets_From_Reversal')['Errors'].mean()
    ax.plot(subset_mean.index, subset_mean, linestyle='-', alpha=0.4, color=colors[i])

# Overlay overall mean and SEM
ax.plot(overall_mean_errors.index, overall_mean_errors, color='blue', linewidth=3, label='Mean Errors (All Files)')
# ax.fill_between(
#     overall_mean_errors.index, 
#     overall_mean_errors - overall_sem_errors, 
#     overall_mean_errors + overall_sem_errors, 
#     color='black', alpha=0.2, label='SEM'
# )

ax.axvline(0, color='black', linestyle='--', label='Reversal Point')
ax.set_xlabel('Pellets from Reversal')
ax.set_ylabel('Number of Errors')
ax.set_title('Overall Mean Errors Across All Files')
ax.legend()
ax.grid()

# Save the figure as an SVG file
output_path = r'C:\Users\meagh\Desktop\output_figure.svg'  # Replace with your desired file path
# fig.savefig(output_path, format='png', bbox_inches='tight')
# plt.savefig('Save.png')
# print(f"Figure saved as {output_path}")

# Show the figure (optional, depending on your needs)
plt.show()
#%%
# Calculate the overall mean and SEM for the final panel
overall_mean_errors = pd.concat(all_mean_errors, axis=1).mean(axis=1, skipna=True)
overall_sem_errors = pd.concat(all_mean_errors, axis=1).sem(axis=1, skipna=True)

# Final panel for the overall mean and SEM
ax = axes[-1]  # Use the last axis
colors = cm.Blues(np.linspace(0.4, 1, len(all_data)))

for i, subset in enumerate(all_data):
    subset_mean = subset.groupby('Pellets_From_Reversal')['Errors'].mean()
    ax.plot(subset_mean.index, subset_mean, linestyle='-', alpha=0.4, color=colors[i])

# Overlay overall mean and SEM
ax.plot(overall_mean_errors.index, overall_mean_errors, color='blue', linewidth=3, label='Mean Errors (All Files)')
ax.fill_between(overall_mean_errors.index, 
                overall_mean_errors - overall_sem_errors, 
                overall_mean_errors + overall_sem_errors, 
                color='blue', alpha=0.2, label='SEM')

ax.axvline(0, color='black', linestyle='--', label='Reversal Point')
ax.set_xlabel('Pellets from Reversal')
ax.set_ylabel('Number of Errors')
ax.set_title('Overall Mean Errors Across All Files')
#ax.legend()
ax.grid()

# Hide any unused axes (in case the number of files isn't a perfect grid)
for j in range(len(csv_files), len(axes) - 1):  # Adjust for last panel
    axes[j].axis('off')

# Adjust layout for readability
plt.tight_layout()
plt.show()



#%%#####################################################
##THIS CODE WORKS FOR VISUALIZING ALL INDIVIDUALS
########################################################
# Get a list of all CSV files in the directory
csv_files = glob.glob(os.path.join(directory, '*.csv'))

# Create a figure for plotting the results
n_files = len(csv_files)
n_cols = 3  # Number of columns for subplots
n_rows = (n_files + n_cols - 1) // n_cols  # Calculate number of rows needed
fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5 * n_rows), sharey=True)
axes = axes.flatten()  # Flatten axes to make indexing easier

# Function to calculate mean and SEM
def calculate_mean_and_sem(plot_data, num_reversals):
    aligned_data = pd.DataFrame()
    for subset in plot_data[:num_reversals]:
        aligned_data = pd.concat([aligned_data, subset.set_index('Pellets_From_Reversal')['Errors']], axis=1)

    mean_errors = aligned_data.mean(axis=1, skipna=True)
    sem_errors = aligned_data.sem(axis=1, skipna=True)
    return mean_errors, sem_errors

# Loop through each CSV file
for i, csv_file in enumerate(csv_files):
    # Load the data from the current CSV file
    data = pd.read_csv(csv_file)

    # Initialize the list to store pellet counts at reversals
    reversals = []

    # Identify reversals
    for j in range(1, len(data)):
        if data.loc[j, 'Active_Poke'] != data.loc[j - 1, 'Active_Poke']:
            reversals.append(data.loc[j, 'Pellet_Count'])

    # Prepare the error data for plotting
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

    # Prepare data for plotting
    plot_data = []
    for reversal in reversals:
        start_pellet = reversal - 15
        end_pellet = reversal + 15
        subset = error_data[(error_data['Pellet_Number'] >= start_pellet) &
                            (error_data['Pellet_Number'] <= end_pellet)].copy()
        subset['Pellets_From_Reversal'] = subset['Pellet_Number'] - reversal
        plot_data.append(subset)

    # Calculate the mean and SEM
    num_reversals_to_average = len(plot_data) #Change to how many reversals you want to plot
    mean_errors, sem_errors = calculate_mean_and_sem(plot_data, num_reversals_to_average)

    # Plotting in the corresponding subplot
    ax = axes[i]
    colors = cm.magma(np.linspace(0, 1, len(plot_data)))

    for subset, color in zip(plot_data, colors):
        ax.plot(subset['Pellets_From_Reversal'], subset['Errors'], marker='o', linestyle='-', alpha=0.5, color=color, label=f'Reversal at Pellet {subset.iloc[10]["Pellet_Number"]}')

    # Overlay mean and SEM
    ax.plot(mean_errors.index, mean_errors, color='black', linewidth=3, label='Mean Errors')
    # Uncomment below if you want to show SEM shading
    # ax.fill_between(mean_errors.index, mean_errors - sem_errors, mean_errors + sem_errors, color='black', alpha=0.2, label='SEM', where=(~mean_errors.isna()))

    ax.axvline(0, color='black', linestyle='--', label='Reversal Point')
    ax.set_xlabel('Pellets from Reversal')
    ax.set_ylabel('Number of Errors')
    ax.set_title(f'Errors Before and After Reversals\n{os.path.basename(csv_file)}')
    #ax.legend()
    ax.grid()

# Hide any unused axes (in case the number of files isn't a perfect grid)
for j in range(i + 1, len(axes)):
    axes[j].axis('off')

# Adjust layout for readability
plt.tight_layout()

# Save the figure as an SVG file
#output_path = r'C:\Users\meagh\Desktop\output_figure.svg'  # Replace with your desired file path
#fig.savefig(output_path, format='png', bbox_inches='tight')
plt.savefig('SaveBandits.png')
#print(f"Figure saved as {output_path}")

plt.show()







#%%**************************************
#THIS CODE WORKS FOR INDIVIDUAL CSV FILES
##***************************************
#%%
# Load the CSV file (replace 'file.csv' with your actual file path)
data = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral\UncategorizedJeffFeb\MSNI_AS2_Jeff_Feb2025.csv')

#%%
# Initialize the list to store pellet counts at reversals
reversals = []

# Iterate through the DataFrame to identify reversals
for i in range(1, len(data)):
    if data.loc[i, 'Active_Poke'] != data.loc[i - 1, 'Active_Poke']:
        reversals.append(data.loc[i, 'Pellet_Count'])

# Prepare the error data for plotting
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

# Define the range for plotting
plot_data = []
for reversal in reversals:
    start_pellet = reversal - 15
    end_pellet = reversal + 15
    subset = error_data[(error_data['Pellet_Number'] >= start_pellet) &
                        (error_data['Pellet_Number'] <= end_pellet)].copy()
    subset['Pellets_From_Reversal'] = subset['Pellet_Number'] - reversal
    plot_data.append(subset)

# Calculate the mean and SEM for reversals
def calculate_mean_and_sem(plot_data, num_reversals):
    aligned_data = pd.DataFrame()
    for subset in plot_data[:num_reversals]:
        aligned_data = pd.concat([aligned_data, subset.set_index('Pellets_From_Reversal')['Errors']], axis=1)

    mean_errors = aligned_data.mean(axis=1, skipna=True)
    sem_errors = aligned_data.sem(axis=1, skipna=True)
    return mean_errors, sem_errors

# Choose the number of reversals to average (all reversals or first 5 reversals)
num_reversals_to_average = len(plot_data)  # Change this to 5 for only the first 5 reversals
mean_errors, sem_errors = calculate_mean_and_sem(plot_data, num_reversals_to_average)

# Plot the results
plt.figure(figsize=(10, 6))
colors = cm.magma(np.linspace(0, 1, len(plot_data)))

for subset, color in zip(plot_data, colors):
    plt.plot(subset['Pellets_From_Reversal'], subset['Errors'], marker='o', linestyle='-', alpha=0.5, color=color, label=f'Reversal at Pellet {subset.iloc[10]["Pellet_Number"]}')

# Overlay mean and SEM
plt.plot(mean_errors.index, mean_errors, color='black', linewidth=3, label='Mean Errors')
#plt.fill_between(mean_errors.index, mean_errors - sem_errors, mean_errors + sem_errors, color='black', alpha=0.2, label='SEM', where=(~mean_errors.isna()))

plt.axvline(0, color='black', linestyle='--', label='Reversal Point')
plt.xlabel('Pellets from Reversal')
plt.ylabel('Number of Errors')
plt.title('Errors Before and After Reversals')
plt.legend()
plt.grid()
plt.show()



#%%
# Initialize variables
pellet_counts = []
error_counts = []
error_count = 0
pellet_number = 0

# Iterate through the rows of the DataFrame
for index, row in data.iterrows():
    event = row['Event']
    active_poke = row['Active_Poke']

    if event == 'Pellet':
        # Increment pellet number
        pellet_number += 1
        # Record the current error count and reset it
        pellet_counts.append(pellet_number)
        error_counts.append(error_count)
        error_count = 0
    elif event in ['Left', 'Right']:
        # Check if the event matches the active poke (correct choice)
        if event != active_poke:
            # Count as an error if it does not match
            error_count += 1

# Plot the results
plt.figure(figsize=(10, 6))
plt.plot(pellet_counts, error_counts, marker='o', linestyle='-', color='b')
plt.xlabel('Pellet Number')
plt.ylabel('Number of Errors')
plt.title('Errors Between Successive Pellets')
plt.grid()
plt.show()