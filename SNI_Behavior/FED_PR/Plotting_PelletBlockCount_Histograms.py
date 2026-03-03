# -*- coding: utf-8 -*-
"""
Created on Sun Aug  4 13:28:01 2024

@author: meagh
"""

import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Directory containing .csv files
directory_sham = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Naive')
directory_sni = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Acute\SNI')

#directory_sham = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Chronic\SHAM')
#directory_sni = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Chronic\SNI')


#directory_sham = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Baseline\SHAM')
#directory_sni = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Baseline\SNI')
#%%
# List to hold the series for each csv file in the SHAM directory
data_frames = []

# Iterate over each file in the directory
for filename in os.listdir(directory_sham):
    if filename.endswith('.csv'):
        filepath = os.path.join(directory_sham, filename)
        # Read the csv file
        df = pd.read_csv(filepath)
        
        # Create a list to store Block_Pellet_Count values that meet the condition
        block_pellet_counts = []

        # Iterate through the rows of the dataframe
        for i in range(len(df) - 1):  # len(df) - 1 to avoid IndexError
            if df.iloc[i + 1]['Block_Pellet_Count'] == 0:
                block_pellet_counts.append(df.iloc[i]['Block_Pellet_Count']) 
        
        # Create a Series with Block_Pellet_Count values and set its name to the filename (without extension)
        series = pd.Series(block_pellet_counts, name=filename.replace('.csv', ''))
        
        # Append the Series to the list of DataFrames
        data_frames.append(series)
        #print(data_frames)

# Combine all series into a DataFrame
result_df_sham = pd.concat(data_frames, axis=1)

#%%
# List to hold the series for each csv file in the SNI directory
data_frames = []

# Iterate over each file in the directory
for filename in os.listdir(directory_sni):
    if filename.endswith('.csv'):
        filepath = os.path.join(directory_sni, filename)
        # Read the csv file
        df = pd.read_csv(filepath)
        
        # Create a list to store Block_Pellet_Count values that meet the condition
        block_pellet_counts = []

        # Iterate through the rows of the dataframe
        for i in range(len(df) - 1):  # len(df) - 1 to avoid IndexError
            if df.iloc[i + 1]['Block_Pellet_Count'] == 0:
                block_pellet_counts.append(df.iloc[i]['Block_Pellet_Count'])
        
        # Create a Series with Block_Pellet_Count values and set its name to the filename (without extension)
        series = pd.Series(block_pellet_counts, name=filename.replace('.csv', ''))
        
        # Append the Series to the list of DataFrames
        data_frames.append(series)
        #print(data_frames)

# Combine all series into a DataFrame
result_df_sni = pd.concat(data_frames, axis=1)

# Save the resulting DataFrame to a new .csv file
#result_df.to_csv('result.csv', index=False)
#%%
print("Data processing complete. Result saved to 'result.csv'.")
#%% Plot/Overlay two histograms
def calculate_average_histogram(df):
    """Calculate the average histogram for a DataFrame."""
    # Define the bin edges. Adjust as needed based on your data range.
    bin_edges = np.arange(df.min().min(), df.max().max() + 2)  # +2 to include the last bin edge

    # Create an empty list to store histograms
    histograms = []

    # Compute histograms for each column
    for column in df.columns:
        data = df[column].dropna()
        hist, _ = np.histogram(data, bins=bin_edges, density= True)
        histograms.append(hist)

    # Convert list of histograms to a numpy array and compute the mean
    histograms_array = np.array(histograms)
    mean_histogram = np.mean(histograms_array, axis=0)

    return bin_edges, mean_histogram

# Load the resulting DataFrames
result_df = result_df_sham #pd.read_csv('result.csv')
result_df2 = result_df_sni #pd.read_csv('result2.csv')  # Assuming 'result2.csv' is your second DataFrame

# Calculate the average histograms
bin_edges1, mean_histogram1 = calculate_average_histogram(result_df)
bin_edges2, mean_histogram2 = calculate_average_histogram(result_df2)

# Create figure and axis objects
plt.figure(figsize=(12, 7))

# Plot the average histograms
plt.bar(bin_edges1[:-1] - 0.2, mean_histogram1, width=0.5, label='Histogram from result_df', edgecolor='black', alpha=0.5)
plt.bar(bin_edges2[:-1] + 0.2, mean_histogram2, width=0.5, label='Histogram from result_df2', edgecolor='black', alpha=0.5)

# Overlay KDEs
sns.kdeplot(result_df.stack(), bw_adjust=0.5, label='KDE for result_df', linestyle='--', color='blue')
sns.kdeplot(result_df2.stack(), bw_adjust=0.5, label='KDE for result_df2', linestyle='--', color='red')

# Add labels and legend
#plt.yscale('log')
#plt.ylim(0.01,10)
plt.title('Average Normalized Histograms and KDE of Block_Pellet_Counts')
plt.xlabel('Block_Pellet_Count')
plt.ylabel('Average Frequency')
plt.legend()
plt.grid(True)
plt.show()
#plt.savefig('HistogramBlockPelletcount_Acute.svg')

#%%
#%%
# Assuming your two datasets are 'data1' and 'data2'
ks_stat, p_value = stats.ks_2samp(result_df.stack(), result_df2.stack())

print(f"KS Statistic: {ks_stat}")
print(f"P-value: {p_value}")