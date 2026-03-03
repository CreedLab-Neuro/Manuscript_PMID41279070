# -*- coding: utf-8 -*-
"""
Created on Thu Oct 10 16:30:36 2024

@author: meagh
"""

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
from numpy.polynomial.polynomial import Polynomial
from scipy.interpolate import UnivariateSpline
from statsmodels.nonparametric.smoothers_lowess import lowess

# Directory containing .csv files
#directory_sham = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Acute\SHAM')
#directory_sni = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Acute\SNI')

directory_sham = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Chronic\SHAM')
directory_sni = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Chronic\SNI')


#directory_sham = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Baseline\SHAM')
#directory_sni = (r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Baseline\SNI')
#%%
# List to hold the series for each csv file in the naive directory
data_frames = []

# Iterate over each file in the directory
for filename in os.listdir(directory_naive):
    if filename.endswith('.csv'):
        filepath = os.path.join(directory_naive, filename)
        # Read the csv file
        df = pd.read_csv(filepath)
        
        # Create a list to store Block_Pellet_Count values that meet the condition
        pellet_price = []

        # Iterate through the rows of the dataframe
        for i in range(len(df) - 1):  # len(df) - 1 to avoid IndexError
            if df.iloc[i]['Event'] == 'Pellet':
                pellet_price.append(df.iloc[i]['FR'])
        
        # Create a Series with Block_Pellet_Count values and set its name to the filename (without extension)
        series = pd.Series(pellet_price, name=filename.replace('.csv', ''))
        
        # Append the Series to the list of DataFrames
        data_frames.append(series)
        #print(data_frames)

# Combine all series into a DataFrame
result_df_sham = pd.concat(data_frames, axis=1)
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
        pellet_price = []

        # Iterate through the rows of the dataframe
        for i in range(len(df) - 1):  # len(df) - 1 to avoid IndexError
            if df.iloc[i]['Event'] == 'Pellet':
                pellet_price.append(df.iloc[i]['FR'])
        
        # Create a Series with Block_Pellet_Count values and set its name to the filename (without extension)
        series = pd.Series(pellet_price, name=filename.replace('.csv', ''))
        
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
        pellet_price = []

        # Iterate through the rows of the dataframe
        for i in range(len(df) - 1):  # len(df) - 1 to avoid IndexError
            if df.iloc[i]['Event'] == 'Pellet':
                pellet_price.append(df.iloc[i]['FR'])
        
        # Create a Series with Block_Pellet_Count values and set its name to the filename (without extension)
        series = pd.Series(pellet_price, name=filename.replace('.csv', ''))
        
        # Append the Series to the list of DataFrames
        data_frames.append(series)
        #print(data_frames)

# Combine all series into a DataFrame
result_df_sni = pd.concat(data_frames, axis=1)

# Save the resulting DataFrame to a new .csv file
#result_df.to_csv('result.csv', index=False)

#print("Data processing complete. Result saved to 'result.csv'.")
#%% Plot/Overlay two histograms
def calculate_average_histogram(df):
    """Calculate the average histogram for a DataFrame."""
    # Define the bin edges. Adjust as needed based on your data range.
    bin_edges = np.arange(df.min().min(), df.max().max() + 2)  # +2 to include the last bin edge
    #bin_edges = [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 13, 15, 17, 20, 22, 25, 28, 32, 36, 40, 45, 50, 56, 62, 69, 77, 86, 95, 106, 118, 131, 145, 161, 178, 220, 243, 270, 300]

    # Create an empty list to store histograms
    histograms = []

    # Compute histograms for each column
    for column in df.columns:
        data = df[column].dropna()
        hist, _ = np.histogram(data, bins=bin_edges, density=True)
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
plt.bar((bin_edges1[:-1]) - 0.2, mean_histogram1, width=0.5, label='Histogram from result_df', edgecolor='black', alpha=0.5)
plt.bar((bin_edges2[:-1]) + 0.2, mean_histogram2, width=0.5, label='Histogram from result_df2', edgecolor='black', alpha=0.5)

# Overlay KDEs
sns.kdeplot(result_df.stack(), bw_adjust=0.5, label='KDE for result_df', linestyle='--', color='blue')
sns.kdeplot(result_df2.stack(), bw_adjust=0.5, label='KDE for result_df2', linestyle='--', color='red')

# Add labels and legend
#plt.xscale('symlog')
plt.xlim(0.00,250)
plt.title('Average Normalized Histograms and KDE of Pellet Price')
plt.xlabel('Pellet Price')
plt.ylabel('Average Frequency')
plt.legend()
plt.grid(True)
#plt.show()
#plt.savefig('HistogramBPelletPrice_AcuteNorm.svg')

#%%
# Updated mapping dictionary
mapping = {
    1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 9: 8,
    10: 9, 12: 10, 13: 11, 15: 12, 17: 13, 20: 14,
    22: 15, 25: 16, 28: 17, 32: 18, 36: 19, 40: 20,
    45: 21, 50: 22, 56: 23, 62: 24, 69: 25, 77: 26,
    86: 27, 95: 28, 106: 29, 118: 30, 131: 31, 145: 32,
    161: 33, 178: 34, 197: 35, 219: 36, 242: 37, 268: 38,
    297: 39, 328: 40, 363: 41, 402: 42, 445: 43, 492: 44,
    545: 45
}

def calculate_average_histogram(df):
    """Calculate the average histogram for a DataFrame."""
    # Define the bin edges. Adjust as needed based on your data range.
    bin_edges = np.arange(df.min().min(), df.max().max() + 2)  # +2 to include the last bin edge
    #bin_edges = [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 12, 13, 15, 17, 20, 22, 25, 28, 32, 36, 40, 45, 50, 56, 62, 69, 77, 86, 95, 106, 118, 131, 145, 161, 178, 220, 243, 270, 300]

    # Create an empty list to store histograms
    histograms = []

    # Compute histograms for each column
    for column in df.columns:
        data = df[column].dropna()
        hist, _ = np.histogram(data, bins=bin_edges, density=True)
        histograms.append(hist)

    # Convert list of histograms to a numpy array and compute the mean
    histograms_array = np.array(histograms)
    mean_histogram = np.mean(histograms_array, axis=0)

    return bin_edges, mean_histogram

# Load the resulting DataFrames
result_df = result_df_sham.replace(mapping) #pd.read_csv('result.csv')
result_df2 = result_df_sni.replace(mapping) #pd.read_csv('result2.csv')  # Assuming 'result2.csv' is your second DataFrame

# Calculate the average histograms
bin_edges1, mean_histogram1 = calculate_average_histogram(result_df)
bin_edges2, mean_histogram2 = calculate_average_histogram(result_df2)

# Create figure and axis objects
plt.figure(figsize=(12, 7))

# Plot the average histograms
plt.bar((bin_edges1[:-1]) - 0.2, mean_histogram1, width=0.5, label='Histogram from result_df', edgecolor='black', alpha=0.5)
plt.bar((bin_edges2[:-1]) + 0.2, mean_histogram2, width=0.5, label='Histogram from result_df2', edgecolor='black', alpha=0.5)

# Overlay KDEs
sns.kdeplot(result_df.stack(), bw_adjust=0.5, label='KDE for result_df', linestyle='--', color='blue')
sns.kdeplot(result_df2.stack(), bw_adjust=0.5, label='KDE for result_df2', linestyle='--', color='red')

# Add labels and legend
#plt.xscale('symlog')
plt.xlim(0.00,50)
plt.title('Average Normalized Histograms and KDE of Pellet Price')
plt.xlabel('Pellet Price')
plt.ylabel('Average Frequency')
plt.legend()
plt.grid(True)
#plt.show()
#plt.savefig('HistogramBPelletPrice_ChronicMapped.svg')

#%%
# Assuming your two datasets are 'data1' and 'data2'
ks_stat, p_value = stats.ks_2samp(mean_histogram1, mean_histogram2)

print(f"KS Statistic: {ks_stat}")
print(f"P-value: {p_value}")

#%% Calculate a demand curve
# Sample DataFrame - replace this with your actual DataFrame
# Each column corresponds to a subject, rows are the prices paid for each pellet
# Replace this line with your DataFrame, e.g. df = pd.read_csv('your_data.csv')
df = result_df_sham

# mapping = {
#     1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 9: 8,
#     10: 9, 12: 10, 13: 11, 15: 12, 17: 13, 20: 14,
#     22: 15, 25: 16, 28: 17, 32: 18, 36: 19, 40: 20,
#     45: 21, 50: 22, 56: 23, 62: 24, 69: 25, 77: 26,
#     86: 27, 95: 28, 106: 29, 118: 30, 131: 31, 145: 32,
#     161: 33, 178: 34, 197: 35, 219: 36, 242: 37, 268: 38,
#     297: 39, 328: 40, 363: 41, 402: 42, 445: 43, 492: 44,
#     545: 45
# }

# df = df.replace(mapping)

# Create the plot
plt.figure(figsize=(10, 6))

# Get the number of subjects (columns)
num_subjects = df.shape[1]

# Loop through each subject (each column in the DataFrame)
for col in df.columns:
    # Drop NaN values if any exist
    prices = df[col].dropna()
    
    # Count the frequency of each unique price for this subject
    price_counts = prices.value_counts().sort_index()  # Sort by price for plotting
    
    # Plot the raw frequency distribution for the subject (Pellet Count on Y-axis, Price Paid on X-axis)
    plt.plot(price_counts.index, price_counts.values, color='blue', alpha=0.3, linewidth=1)

# For the average raw frequency distribution across subjects:
# Initialize a series to hold cumulative counts
all_price_counts = pd.Series(dtype=float)

# Initialize a DataFrame to hold the counts for each subject (for SEM calculation)
price_counts_df = pd.DataFrame()

# Loop through each subject and sum up price counts
for col in df.columns:
    prices = df[col].dropna()
    price_counts = prices.value_counts().sort_index()
    
    # Add the price counts to the cumulative total
    all_price_counts = all_price_counts.add(price_counts, fill_value=0)
    
    # Store the price counts in a DataFrame to calculate SEM later
    price_counts_df = pd.concat([price_counts_df, price_counts], axis=1)

# Divide the cumulative counts by the number of subjects to get the average
average_price_counts = all_price_counts / num_subjects

# Calculate the Standard Error of the Mean (SEM)
sem_price_counts = price_counts_df.std(axis=1) / np.sqrt(num_subjects)

# Plot the average raw frequency distribution (Pellet Count on Y-axis, Price Paid on X-axis)
# Plot the average raw frequency distribution with error bars (SEM)
plt.errorbar(average_price_counts.index, average_price_counts.values, yerr=sem_price_counts, 
             fmt='o', color='blue', ecolor='black', elinewidth=1.5, capsize=3, label='Average with SEM')

# Fit a Univariate Spline, s=0 forces the spline to pass through all points
spline = UnivariateSpline(x, y, s=0)

# Generate x values for smooth curve
x_smooth4 = np.linspace(x.min(), x.max(), 300)
y_smooth4 = spline(x_smooth4)

# Plot the smoothed curve (Spline interpolation line)
plt.plot(x_smooth4, y_smooth4, color='green', linestyle='--', linewidth=2, label='Smoothed Fit (Spline)')

# Now add a smoothed line of best fit using polynomial regression (degree 3 as an example)
x = average_price_counts.index
y = average_price_counts.values

# Fit a polynomial curve (degree 3)
p = Polynomial.fit(x, y, deg=1)

# Generate x values for smooth curve
x_smooth = np.linspace(x.min(), x.max(), 300)
y_smooth = p(x_smooth)

# Plot the smoothed curve (Polynomial regression line)
plt.plot(x_smooth, y_smooth, color='green', linestyle='--', linewidth=2, label='Smoothed Fit')

# Customize the plot
# Customize the plot
plt.title('Average Pellet Count vs Price Paid by Subject')
plt.xlabel('Price Paid')  # X-axis label
plt.yscale('log')
plt.xscale('log')
plt.xlim(0,1000)
plt.ylim(0.1, 200)
plt.ylabel('Average Pellet Count')  # Y-axis label
plt.grid(True)
plt.savefig('DemandCurve_SHAM_Acute.svg')


#%% Calculate a demand curve
# Sample DataFrame - replace this with your actual DataFrame
# Each column corresponds to a subject, rows are the prices paid for each pellet
# Replace this line with your DataFrame, e.g. df = pd.read_csv('your_data.csv')
df2 = result_df_sni

# mapping = {
#     1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 9: 8,
#     10: 9, 12: 10, 13: 11, 15: 12, 17: 13, 20: 14,
#     22: 15, 25: 16, 28: 17, 32: 18, 36: 19, 40: 20,
#     45: 21, 50: 22, 56: 23, 62: 24, 69: 25, 77: 26,
#     86: 27, 95: 28, 106: 29, 118: 30, 131: 31, 145: 32,
#     161: 33, 178: 34, 197: 35, 219: 36, 242: 37, 268: 38,
#     297: 39, 328: 40, 363: 41, 402: 42, 445: 43, 492: 44,
#     545: 45
# }

# df2 = df2.replace(mapping)

# Create the plot
plt.figure(figsize=(10, 6))

# Get the number of subjects (columns)
num_subjects = df2.shape[1]

# Loop through each subject (each column in the DataFrame)
for col in df2.columns:
    # Drop NaN values if any exist
    prices = df2[col].dropna()
    
    # Count the frequency of each unique price for this subject
    price_counts = prices.value_counts().sort_index()  # Sort by price for plotting
    
    # Plot the raw frequency distribution for the subject (Pellet Count on Y-axis, Price Paid on X-axis)
    plt.plot(price_counts.index, price_counts.values, color='red', alpha=0.3, linewidth=1)

# For the average raw frequency distribution across subjects:
# Initialize a series to hold cumulative counts
all_price_counts = pd.Series(dtype=float)

# Initialize a DataFrame to hold the counts for each subject (for SEM calculation)
price_counts_df = pd.DataFrame()

# Loop through each subject and sum up price counts
for col in df2.columns:
    prices = df2[col].dropna()
    price_counts = prices.value_counts().sort_index()
    
    # Add the price counts to the cumulative total
    all_price_counts = all_price_counts.add(price_counts, fill_value=0)
    
    # Store the price counts in a DataFrame to calculate SEM later
    price_counts_df = pd.concat([price_counts_df, price_counts], axis=1)

# Divide the cumulative counts by the number of subjects to get the average
average_price_counts = all_price_counts / num_subjects

# Calculate the Standard Error of the Mean (SEM)
sem_price_counts = price_counts_df.std(axis=1) / np.sqrt(num_subjects)

# Plot the average raw frequency distribution (Pellet Count on Y-axis, Price Paid on X-axis)
# Plot the average raw frequency distribution with error bars (SEM)
plt.errorbar(average_price_counts.index, average_price_counts.values, yerr=sem_price_counts, 
             fmt='o', color='black', ecolor='black', elinewidth=1.5, capsize=3, label='Average with SEM')

# Now add a smoothed line of best fit using polynomial regression (degree 3 as an example)
x = average_price_counts.index
y = average_price_counts.values

# Fit a polynomial curve (degree 3)
p = Polynomial.fit(x, y, deg=1)

# Generate x values for smooth curve
x_smooth = np.linspace(x.min(), x.max(), 300)
y_smooth = p(x_smooth)

# Plot the smoothed curve (Polynomial regression line)
plt.plot(x_smooth, y_smooth, color='black', linestyle='--', linewidth=2, label='Smoothed Fit')

# Fit a Univariate Spline, s=0 forces the spline to pass through all points
spline = UnivariateSpline(x, y, s=0)

# Generate x values for smooth curve
x_smooth2 = np.linspace(x.min(), x.max(), 300)
y_smooth2 = spline(x_smooth)

# Plot the smoothed curve (Spline interpolation line)
plt.plot(x_smooth2, y_smooth2, color='green', linestyle='--', linewidth=2, label='Smoothed Fit (Spline)')

# Now add a smoothed line using LOESS (Locally Weighted Scatterplot Smoothing)
x = average_price_counts.index
y = average_price_counts.values

# Perform LOESS smoothing (frac determines the degree of smoothing, adjust between 0-1)
smoothed = lowess(y, x, frac=0.3)

# Extract the smoothed x and y values
x_smooth3 = smoothed[:, 0]
y_smooth3 = smoothed[:, 1]

# Plot the smoothed curve (LOESS fit line)
plt.plot(x_smooth3, y_smooth3, color='purple', linestyle='--', linewidth=2, label='Smoothed Fit (LOESS)')



# Customize the plot
plt.title('Average Pellet Count vs Price Paid by Subject')
plt.xlabel('Price Paid')  # X-axis label
plt.yscale('log')
plt.xscale('log')
plt.xlim(0,1000)
plt.ylim(0.1, 200)
plt.ylabel('Average Pellet Count')  # Y-axis label
plt.grid(True)

# Show the plot (no legend)
#plt.show()
plt.savefig('DemandCurve_SNI_Acute.svg')