# -*- coding: utf-8 -*-
"""
Created on Thu Dec 26 00:39:50 2024

@author: meagh
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import pandas as pd
from datetime import timedelta
#%%
##Slicing from specified start time
##########################################
def filter_csv_by_start_time(input_csv_path, start_time_str, output_csv_path):
    """
    Filters a CSV file to include only rows within 72 hours of a specified start time
    and saves the filtered DataFrame to a new CSV file.

    Parameters:
    - input_csv_path: Path to the input CSV file.
    - start_time_str: Start time as a string in the format "MM:DD:YYYY hh:mm:ss".
    - output_csv_path: Path to save the filtered CSV file.
    """
    # Load the CSV file
    df = pd.read_csv(input_csv_path)

    # Ensure the leftmost column is parsed as datetime
    timestamp_col = "MM:DD:YYYY hh:mm:ss"
    if timestamp_col not in df.columns:
        raise ValueError(f"Column '{timestamp_col}' not found in the CSV file.")
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], format='%m/%d/%Y %H:%M:%S')

    # Convert the specified start time to a datetime object
    start_time = pd.to_datetime(start_time_str, format='%m/%d/%Y %H:%M:%S')

    # Calculate the cutoff time (72 hours after the specified start time)
    cutoff_time = start_time + timedelta(hours=72)

    # Filter the DataFrame to include only rows within the specified time range
    df_filtered = df[(df[timestamp_col] >= start_time) & (df[timestamp_col] <= cutoff_time)]

    # Save the filtered DataFrame to the specified output path
    df_filtered.to_csv(output_csv_path, index=False)

    print(f"Filtered CSV saved to: {output_csv_path}")

# Example usage
input_csv = r'C:\Users\meagh\Box\CreedLabBoxDrive\Accumbal_Pain_Project\03_Behavioral Data\04_Projects\03_rPR_Acute Surgical Pain\Post_Pain\CE8a_FED006_090321_02.CSV'  # Path to the input CSV file
start_time = '09/04/2021 19:00:00'  # Specified start time in the format "MM:DD:YYYY hh:mm:ss"
output_csv = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_ASP\Female_Post_FED006_090321.csv'  # Path to save the filtered CSV file

filter_csv_by_start_time(input_csv, start_time, output_csv)

#%% Modified Code to fix conversion error in Reversal files
def filter_csv_by_start_time(input_csv_path, start_time_str, output_csv_path):
    """
    Filters a CSV file to include only rows within 72 hours of a specified start time
    and saves the filtered DataFrame to a new CSV file.

    Parameters:
    - input_csv_path: Path to the input CSV file.
    - start_time_str: Start time as a string in the format "MM:DD:YYYY hh:mm:ss".
    - output_csv_path: Path to save the filtered CSV file.
    """
    # Load the CSV file
    df = pd.read_csv(input_csv_path)

    # Ensure the leftmost column is parsed as datetime
    timestamp_col = "MM:DD:YYYY hh:mm:ss"
    if timestamp_col not in df.columns:
        raise ValueError(f"Column '{timestamp_col}' not found in the CSV file.")
    
    # Let pandas automatically infer the timestamp format
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors='coerce')

    # Check for any NaT (Not a Time) values in the column
    if df[timestamp_col].isna().any():
        raise ValueError("Some timestamps could not be parsed. Please verify the input data format.")

    # Convert the specified start time to a datetime object
    start_time = pd.to_datetime(start_time_str, format='%m/%d/%Y %H:%M:%S')

    # Calculate the cutoff time (72 hours after the specified start time)
    cutoff_time = start_time + timedelta(hours=96)

    # Filter the DataFrame to include only rows within the specified time range
    df_filtered = df[(df[timestamp_col] >= start_time) & (df[timestamp_col] <= cutoff_time)]

    # Save the filtered DataFrame to the specified output path
    df_filtered.to_csv(output_csv_path, index=False)

    print(f"Filtered CSV saved to: {output_csv_path}")

# Example usage
input_csv = r'C:\Users\meagh\OneDrive\Documents\RevTest\MSNI_FED001_081424_01.csv'  # Path to the input CSV file
start_time = '08/14/2024 17:00:00'  # Specified start time in the format "MM:DD:YYYY hh:mm:ss"
output_csv = r'C:\Users\meagh\OneDrive\Documents\RevTest\MSNI_FED001_081424_72h.csv'  # Path to save the filtered CSV file

filter_csv_by_start_time(input_csv, start_time, output_csv)

#%%


def slice_csv_to_72h(input_csv_path, output_directory, output_filename):
    """
    Slices a CSV file to include only the first 72 hours of data and saves it to a new directory.

    Parameters:
    - input_csv_path: Path to the input CSV file.
    - output_directory: Path to the directory where the new CSV will be saved.
    - output_filename: Name for the new CSV file (e.g., "sliced_data.csv").
    """
    # Load the CSV file
    df = pd.read_csv(input_csv_path)

    # Ensure the leftmost column is parsed as datetime
    timestamp_col = "MM:DD:YYYY hh:mm:ss"
    if timestamp_col not in df.columns:
        raise ValueError(f"Column '{timestamp_col}' not found in the CSV file.")
    df[timestamp_col] = pd.to_datetime(df[timestamp_col], format='%m/%d/%Y %H:%M:%S')  # Updated format string

    # Get the starting timestamp
    start_time = df[timestamp_col].min()

    # Calculate the cutoff time (72 hours after the start)
    cutoff_time = start_time + timedelta(hours=72)

    # Filter the DataFrame to include only rows within the first 72 hours
    df_sliced = df[df[timestamp_col] <= cutoff_time]

    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Save the sliced DataFrame to the new directory with the specified filename
    output_path = os.path.join(output_directory, output_filename)
    df_sliced.to_csv(output_path, index=False)

    print(f"Sliced CSV saved to: {output_path}")

# Example usage
input_csv = r'C:\Users\meagh\OneDrive\Documents\RevTest\MSNI_FED024_092423_mod.csv'  # Path to the input CSV file
output_dir = r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Reversal\RevNeutral'  # Directory to save the new CSV
output_file = 'MSNI_PostBandit_FED016ch.csv'  # New filename for the shortened CSV

slice_csv_to_72h(input_csv, output_dir, output_file)


#%%
# Function to filter dataframe by timestamp range
def filter_dataframe_by_time(input_csv, start_time, end_time, output_folder, output_filename):
    """
    Filters a CSV file by a specified timestamp range and saves the result to a new file.

    Parameters:
    - input_csv: Path to the input CSV file.
    - start_time: Start time as a string in the format 'MM:DD:YYYY hh:mm:ss'.
    - end_time: End time as a string in the format 'MM:DD:YYYY hh:mm:ss'.
    - output_folder: Path to the folder where the modified CSV will be saved.
    - output_filename: Filename for the saved CSV file.
    """
    # Load the CSV file into a DataFrame
    df = pd.read_csv(input_csv)

    # Ensure the first column is parsed as datetime
    df.iloc[:, 0] = pd.to_datetime(df.iloc[:, 0], format='%m:%d:%Y %H:%M:%S')

    # Convert the input start and end times to datetime
    start_datetime = pd.to_datetime(start_time, format='%m:%d:%Y %H:%M:%S')
    end_datetime = pd.to_datetime(end_time, format='%m:%d:%Y %H:%M:%S')

    # Filter the DataFrame based on the time range
    filtered_df = df[(df.iloc[:, 0] >= start_datetime) & (df.iloc[:, 0] <= end_datetime)]

    # Ensure the output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Save the filtered DataFrame to the specified output file
    output_path = os.path.join(output_folder, output_filename)
    filtered_df.to_csv(output_path, index=False)

    print(f"Filtered CSV saved to: {output_path}")

# Example usage
input_csv = r'C:\path\to\your\input.csv'  # Replace with the path to your input CSV
start_time = '01:01:2024 08:00:00'       # Replace with your desired start time
end_time = '01:01:2024 18:00:00'         # Replace with your desired end time
output_folder = r'C:\path\to\output\folder'  # Replace with your desired output folder
output_filename = 'filtered_output.csv'  # Replace with your desired output filename

filter_dataframe_by_time(input_csv, start_time, end_time, output_folder, output_filename)
#%%
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