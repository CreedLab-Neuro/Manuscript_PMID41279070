# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 23:54:44 2024

@author: meagh
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import pingouin as pg
import statsmodels.api as sm

#%%
#%% Import dataframe from .csv file; change file location as needed
df = pd.read_csv(r'C:\Users\goffj\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\Activity_Monitor\Metformin\MetforminPIR.csv')
#%% Headers in CSV include 'Num' for index, and average values of the SNI and CTRL groups with SEM calculated
##This is just visualization, not really calculating anything new

x = df['']
UA = df['All']
A_err = df['All_SEM']
#UC = df['SNI']
#C_err = df['SNI_SEM']


#%%
fig, ax = plt.subplots()
ax.plot(x, UA, '-')
ax.fill_between(x, UA - A_err, UA + A_err, alpha=0.2)
#ax.plot(x, UC, '-')
#ax.fill_between(x, UC - C_err, UC + C_err, alpha=0.2)
plt.xlim(0,248)

plt.savefig('PostSurgicalRecoveryLex.eps')
#%% Import dataframe from .csv file; change file location as needed
df = pd.read_csv(r'C:\Users\meagh\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\Activity_Monitor\Chronic_SNI\PIR_Chronic_Summary.csv')
#%% Headers in CSV include 'Num' for index, and average values of the SNI and CTRL groups with SEM calculated
##This is just visualization, not really calculating anything new

x = df['Hour']
UA = df['CTRL_VEH']
A_err = df['CTRL_VEH_SEM']
UC = df['SNI_VEH']
C_err = df['SNI_VEH_SEM']
UB = df['SNI_MET']
B_err = df['SNI_MET_SEM']

fig, ax = plt.subplots()
ax.plot(x, UA, '-')
ax.fill_between(x, UA - A_err, UA + A_err, alpha=0.2)
ax.plot(x, UB, '-')
ax.fill_between(x, UB - B_err, UB + B_err, alpha=0.2)
ax.plot(x, UC, '-')
ax.fill_between(x, UC - C_err, UC + C_err, alpha=0.2)
plt.xlim(0,30)

plt.savefig('PIR_Metformin2.eps')
#%% Now visualize the individual mice for each condition

#CTRL MALES
A = df['CTRL_M_A04']
B = df['CTRL_M_53D']
C = df['CTRL_M_58E']
D = df['CTRL_M_575']
E = df['CTRL_M_576']

#SNI MALES
F = df['SNI_M_59e']
G = df['SNI_M_530']
H = df['SNI_M_541']
I = df['SNI_M_547']
J = df['SNI_F_5a3'] #This is a typeo in original sheet too tired

#CTRL Females
K = df['CTRL_F_55C']
L = df['CTRL_F_56C']
M = df['CTRL_F_59F']
N = df['CTRL_F_536']
O = df['CTRL_F_A0D']
P = df['CTRL_F_5a2']

#SNI Females
Q = df['SNI_F_50D']
R = df['SNI_F_50E']
S = df['SNI_F_A22']
T = df['SNI_F_B5F']
U = df['SNI_F_B65']
V = df['SNI_F_6F5']




# Initialise the subplot function using number of rows and columns 
figure, axis = plt.subplots(2, 2) 
  
# Pull out which items are control males (from A-Z above)
# Add a title, set the axes
axis[0, 0].plot(x, A, '-')
axis[0, 0].plot(x, B, '-')
axis[0, 0].plot(x, C, '-')
axis[0, 0].plot(x, D, '-')
axis[0, 0].plot(x, E, '-')

axis[0, 0].set_title("SHAM Males") 
axis[0,0].set_xlim(0,120)
axis[0,0].set_ylim(-5, 60)

# Pull out which items are SNI males (from A-Z above)
# Add a title, set the axes
axis[0, 1].plot(x, F, '-')
axis[0, 1].plot(x, G, '-')
axis[0, 1].plot(x, H, '-')
axis[0, 1].plot(x, I, '-')
axis[0, 1].plot(x, J, '-')

axis[0,1].set_title("SNI Males") 
axis[0,1].set_xlim(0,120)
axis[0,1].set_ylim(-5, 60)

# Pull out which items are CTRL females (from A-Z above)
# Add a title, set the axes
axis[1, 0].plot(x, K, '-')
axis[1, 0].plot(x, L, '-')
axis[1, 0].plot(x, M, '-')
axis[1, 0].plot(x, N, '-')
axis[1, 0].plot(x, O, '-')
axis[1, 0].plot(x, P, '-')

axis[1,0].set_title("SHAM Males") 
axis[1,0].set_xlim(0,120)
axis[1,0].set_ylim(-5, 60)

# Pull out which items are SNI females (from A-Z above)
# Add a title, set the axes
axis[1, 1].plot(x, Q, '-')
axis[1, 1].plot(x, R, '-')
axis[1, 1].plot(x, S, '-')
axis[1, 1].plot(x, T, '-')
axis[1, 1].plot(x, U, '-')
axis[1, 1].plot(x, V, '-')

axis[1,1].set_title("SNI Females") 
axis[1,1].set_xlim(0,120)
axis[1,1].set_ylim(-5, 60)

plt.savefig('PIR_Chronic_IndividualBreakdown.eps')
