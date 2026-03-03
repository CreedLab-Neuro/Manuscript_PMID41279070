# -*- coding: utf-8 -*-
"""
Created on Thu Dec 26 00:58:36 2024

@author: meagh
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_binned_mean_choices_with_active_poke(dataframe, bin_size=4):
    """
    Plots a line graph with binned 'Pellet_Count' on the X-axis and mean choices (Left = 0, Right = 1) on the Y-axis,
    with an overlay of 'Active_Poke' values.

    Parameters:
    - dataframe: A Pandas DataFrame containing 'Pellet_Count', 'Event', and 'Active_Poke' columns.
    - bin_size: The size of bins for grouping Pellet_Count (default is 5).
    """
    # Filter the DataFrame to include only rows where 'Event' is 'Left' or 'Right'
    choices = dataframe[dataframe['Event'].isin(['Left', 'Right'])].copy()

    # Map 'Event' to numerical values (0 for Left, 1 for Right)
    choices['Choice_Value'] = choices['Event'].map({'Left': 0, 'Right': 1})

    # Create bins for 'Pellet_Count'
    choices['Pellet_Bin'] = (choices['Pellet_Count'] // bin_size) * bin_size

    # Group by bins and calculate mean choice value
    binned_means = choices.groupby('Pellet_Bin')['Choice_Value'].mean().reset_index()

    # Map 'Active_Poke' to numerical values (0 for Left, 1 for Right)
    dataframe['Active_Poke_Value'] = dataframe['Active_Poke'].map({'Left': 0, 'Right': 1})

    # Bin 'Pellet_Count' for Active_Poke
    dataframe['Pellet_Bin'] = (dataframe['Pellet_Count'] // bin_size) * bin_size

    # Group by bins and calculate mean Active_Poke value
    binned_active_poke = dataframe.groupby('Pellet_Bin')['Active_Poke_Value'].mean().reset_index()

    # Plot the results
    plt.figure(figsize=(10, 6))

    # Plot mean choices
    plt.plot(binned_means['Pellet_Bin'], binned_means['Choice_Value'], marker='o', linestyle='-', color='blue', alpha=0.7, label="Mean Choices (0 = Left, 1 = Right)")

    # Overlay Active_Poke
    plt.plot(binned_active_poke['Pellet_Bin'], binned_active_poke['Active_Poke_Value'], marker='o', linestyle='-', color='red', alpha=0.7, label="Active Poke (0 = Left, 1 = Right)")

    # Customize the plot
    plt.xlabel(f"Pellet Count (Binned by {bin_size})")
    plt.ylabel("Mean Value (0 = Left, 1 = Right)")
    plt.title("Mean Choices and Active Poke by Binned Pellet Count {input_csv}")
    plt.ylim(0, 1)
    plt.legend()
    plt.grid(alpha=0.5)
    plt.show()

# Example usage
# Load your DataFrame (replace with your actual data)
input_csv = r'C:\Users\meagh\OneDrive\Documents\RevTest\MSNI_FED024_092423_mod.csv'  # Replace with the path to your CSV file
df = pd.read_csv(input_csv)

# Plot the graph
plot_binned_mean_choices_with_active_poke(df, bin_size=4)
#%%




#%%
# Example usage
# Load your DataFrame (replace with your actual data)
input_csv = r'C:\Users\meagh\OneDrive\Documents\CE6_FED003_041421_02.csv'  # Replace with the path to your CSV file
df = pd.read_csv(input_csv)


# Plot the graph
plot_left_right_choices(df)