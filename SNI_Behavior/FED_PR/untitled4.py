# -*- coding: utf-8 -*-
"""
Created on Mon Aug  5 07:42:26 2024

@author: meagh
"""

import pandas as pd
import os

# Directory containing .csv files
directory = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Chronic')
#%%
# List to hold data for each file
data_list = []

# Iterate over each file in the directory
for filename in os.listdir(directory):
    if filename.endswith('.csv'):
        # Extract file name without extension
        file_name_without_ext = os.path.splitext(filename)[0]
        
        # Determine 'Sex' based on file name
        sex = 'M' if 'M' in file_name_without_ext else 'F'
        
        # Determine 'Group' based on file name
        if 'SHAM' in file_name_without_ext:
            group = 'SHAM'
        elif 'SNI' in file_name_without_ext:
            group = 'SNI'
        else:
            group = 'Unknown'
        
        # Read the csv file
        file_path = os.path.join(directory, filename)
        df = pd.read_csv(file_path)
        
        # Calculate 'Pellets'
        pellets = df['Events'].str.contains('Pellet').sum()
        
        # Calculate 'PPP1'
        binary_left_pokes_sum = df['Binary_Left_Pokes'].sum()
        ppp1 = binary_left_pokes_sum / pellets if pellets > 0 else 0
        
        # Calculate 'PPP2'
        ppp2 = df['Events'].str.contains('oke').sum() / pellets if pellets > 0 else 0
        
        # Calculate 'Accuracy'
        correct_pokes = df['Correct_Poke'].sum()
        total_pokes = df['Binary_Left_Pokes'].sum() + df['Binary_Right_Pokes'].sum()
        accuracy = correct_pokes / total_pokes if total_pokes > 0 else 0
        
        # Create a dictionary for the current file
        file_data = {
            'File': filename,
            'Sex': sex,
            'Group': group,
            'Pellets': pellets,
            'PPP1': ppp1,
            'PPP2': ppp2,
            'Accuracy': accuracy
        }
        
        # Append the dictionary to the list
        data_list.append(file_data)

# Create a DataFrame from the list of dictionaries
df_summary = pd.DataFrame(data_list)

# Save the DataFrame to a new .csv file
df_summary.to_csv('summary_metadata.csv', index=False)

print("Summary DataFrame created and saved to 'summary_metadata.csv'.")
