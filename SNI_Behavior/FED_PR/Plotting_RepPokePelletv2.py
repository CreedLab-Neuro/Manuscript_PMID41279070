# -*- coding: utf-8 -*-
"""
Created on Sat Aug  3 19:59:53 2024

@author: meagh
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm

#%% # Load the data 

# FOR SNI Example
#df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Baseline\May24_FED6_FSNI_Baseline.csv')
#df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Acute\May24_FED6_FSNI_1Week.csv')
#df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Chronic\JMTJune24_FED06_FSNI.csv')

# FOR SHAM Example
#df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Baseline\May24_FED10_FSHAM_Baseline.csv')
#df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Acute\May24_FED10_FSHAM_1Week.csv')
#df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Chronic\JMTJune24_FED010_FSHAM.csv')

#df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Baseline\May24_FED34_MSHAM_Baseline.csv')
df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_PR\Acute\May24_FED34_MSHAM_1Week.csv')
#df = pd.read_csv(r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Dopamine_Pain_Project\Behavior\NAChBac PR\Cohort 1\Late Post-Rescue\FED48 F SNI\PR\FED002_120924_00.csv')


#%%
# Convert the date timestamp column to datetime format
#df['MM:DD:YYYY hh:mm:ss'] = pd.to_datetime(df['MM:DD:YYYY hh:mm:ss'], format='%m/%d/%Y %H:%M')
df['MM:DD:YYYY hh:mm:ss'] = pd.to_datetime(df['MM:DD:YYYY hh:mm:ss'], errors='coerce')

# Filter data for "Pellet" events
pellet_df = df[df['Event'] == 'Pellet']

# Filter data for "Left" events 
# Depending on the file type, there are two ways to do this, version 1 or version 2

# version 1
left_df = df[df['Event'] == 'Left']  #Left/Pokes

# version 2
#left_df = df[df['Binary_Left_Pokes'] == 1]

# Define the color map and normalization
norm = plt.Normalize(vmin=-10, vmax=40)
cmap = cm.get_cmap('Greens')

# Normalize the 'Block Pellet Count' for color mapping
pellet_df['Color'] = pellet_df['Block_Pellet_Count'].clip(upper=40).apply(lambda x: cmap(norm(x)))

# Create the figure and subplots
fig, axs = plt.subplots(nrows=2, ncols=1, sharex=True, figsize=(12, 12))

# First subplot: Scatter plot for "Pellet" events
scatter = axs[1].scatter(
    pellet_df['MM:DD:YYYY hh:mm:ss'],
    pellet_df['Block_Pellet_Count'],
    c=pellet_df['Block_Pellet_Count'].clip(upper=40),
    cmap='Greens',
    norm=norm
)

# Add shading for specific times of the day
start_time = pd.to_datetime('07:00:00').time()
end_time = pd.to_datetime('19:00:00').time()

# Get the minimum and maximum timestamps for plotting bounds
plot_start = pellet_df['MM:DD:YYYY hh:mm:ss'].min()
plot_end = pellet_df['MM:DD:YYYY hh:mm:ss'].max()

# Create shaded regions for all days in the range
for day in pd.date_range(start=plot_start.date(), end=plot_end.date()):
    start_datetime = pd.Timestamp.combine(day, start_time)
    end_datetime = pd.Timestamp.combine(day, end_time)
    axs[1].axvspan(start_datetime, end_datetime, color='gray', alpha=0.2)

# Second subplot: Vertical lines for "Left" events
for timestamp in left_df['MM:DD:YYYY hh:mm:ss']:
    axs[0].axvline(x=timestamp, color='black', linestyle='-', linewidth=0.1, alpha=0.7)

# Add a color bar to the first subplot
#cbar = plt.colorbar(scatter, ax=axs[0], label='Block Pellet Count')
cbar = plt.colorbar(scatter, ax=axs[1], label='Block Pellet Count')

# Label the axes
axs[1].set_ylabel('Block Pellet Count')
axs[0].set_ylabel('Active Pokes')
#axs[1].set_xlabel('Date and Time')

#Set the limits of the graphs
axs[1].set_ylim([0, 60])

# Rotate date labels for better readability in the x-axis
plt.setp(axs[1].xaxis.get_majorticklabels(), rotation=45)

# Title of the plot
#axs[0].set_title('Scatter Plot of Pellet Events with Block Pellet Count')
axs[0].set_title('JMTJune24_FED10_FSHAM')

# Show the plot
plt.tight_layout()
#plt.savefig('PokePelletPlot_Nachbac_ResidenceTalk.svg')