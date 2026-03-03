# -*- coding: utf-8 -*-
"""
Created on Fri Aug  1 14:25:08 2025

@author: meaghan.creed
"""
# Directories
sham_dir = r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Bandit\TrickyBandit\SHAM'
sni_dir = r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Bandit\TrickyBandit\SNI'

#%%
# Q-learning model fitting from scratch (clean slate) with α+, α−, and flexible Q-init
# Dependencies
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import minimize
from glob import glob

# Adjustable parameters
TRIAL_BIN = 5  # Adjust trial binning for visualization

# Directories (replace with real paths before running)
sham_dir = r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Bandit\TrickyBandit\SHAM'
sni_dir = r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Bandit\TrickyBandit\SNI'

# Load and preprocess data
def load_mouse_data(file_path):
    df = pd.read_csv(file_path)
    df = df[df['Event'].isin(['Left', 'Right', 'Pellet'])].copy()
    df['Choice'] = df['Event'].where(df['Event'].isin(['Left', 'Right']))
    df['Reward'] = df['Event'].eq('Pellet').astype(int)
    df['Choice'].fillna(method='ffill', inplace=True)
    df = df[df['Event'].isin(['Left', 'Right'])].copy()
    return df.reset_index(drop=True)

# Q-learning negative log-likelihood with separate α+, α−
def q_learning_negloglik(params, choices, rewards):
    alpha_pos, alpha_neg, beta, kappa, q_init = params
    q = {'Left': q_init, 'Right': q_init}
    last_choice = None
    nll = 0

    for choice, reward in zip(choices, rewards):
        p = {}
        for c in ['Left', 'Right']:
            pers = kappa if last_choice == c else 0
            p[c] = np.exp(beta * (q[c] + pers))
        p_sum = p['Left'] + p['Right']
        p_choice = p[choice] / p_sum

        nll -= np.log(p_choice + 1e-10)

        delta = reward - q[choice]
        alpha = alpha_pos if delta > 0 else alpha_neg
        q[choice] += alpha * delta

        last_choice = choice

    return nll

# Fit model to single mouse
def fit_q_learning_model(df):
    choices = df['Choice'].values
    rewards = df['Reward'].values
    init_params = [0.3, 0.1, 3.0, 0.0, 0.5]  # α+, α−, β, κ, Q_init
    bounds = [(0, 1), (0, 1), (0.01, 20), (-5, 5), (0, 1)]
    result = minimize(q_learning_negloglik, init_params, args=(choices, rewards), bounds=bounds)
    return result.x

# Simulate choice probabilities using fitted parameters
def simulate_q_learning(params, choices):
    alpha_pos, alpha_neg, beta, kappa, q_init = params
    q = {'Left': q_init, 'Right': q_init}
    last_choice = None
    pred_probs = []

    for _ in choices:
        p = {}
        for c in ['Left', 'Right']:
            pers = kappa if last_choice == c else 0
            p[c] = np.exp(beta * (q[c] + pers))
        p_sum = p['Left'] + p['Right']
        prob_left = p['Left'] / p_sum
        pred_probs.append(prob_left)

        simulated_choice = 'Left' if np.random.rand() < prob_left else 'Right'
        reward = 1 if np.random.rand() < 0.5 else 0  # assume 50% reward probability in simulation

        delta = reward - q[simulated_choice]
        alpha = alpha_pos if delta > 0 else alpha_neg
        q[simulated_choice] += alpha * delta

        last_choice = simulated_choice

    return pred_probs

# Plot actual vs predicted choices
def plot_choices(df, pred_probs, mouse_name):
    df = df.reset_index(drop=True)
    bins = np.arange(0, len(df), TRIAL_BIN)
    actual = df['Choice'].eq('Left').astype(int).groupby(df.index // TRIAL_BIN).mean()
    predicted = pd.Series(pred_probs).groupby(np.arange(len(pred_probs)) // TRIAL_BIN).mean()

    plt.figure(figsize=(8, 4))
    plt.plot(actual.values, label='Actual Left', marker='o')
    plt.plot(predicted.values, label='Predicted Left', marker='o')
    plt.title(f"Mouse: {mouse_name}")
    plt.xlabel(f"Trial bin (every {TRIAL_BIN} trials)")
    plt.ylabel("P(Left)")
    plt.legend()
    plt.tight_layout()
    plt.show()

# Run full model pipeline for a group
def run_model(directory, group):
    param_list = []
    all_files = glob(os.path.join(directory, "*.csv"))

    for file_path in all_files:
        mouse_name = os.path.splitext(os.path.basename(file_path))[0]
        df = load_mouse_data(file_path)
        if len(df) < 20:
            continue

        fitted_params = fit_q_learning_model(df)
        pred_probs = simulate_q_learning(fitted_params, df['Choice'].values)
        plot_choices(df, pred_probs, f"{group}_{mouse_name}")

        param_list.append({
            'Mouse': mouse_name,
            'Group': group,
            'Alpha_Pos': fitted_params[0],
            'Alpha_Neg': fitted_params[1],
            'Beta': fitted_params[2],
            'Stickiness': fitted_params[3],
            'Q_init': fitted_params[4]
        })

    return pd.DataFrame(param_list)

# === Run and export ===
sham_params = run_model(sham_dir, 'SHAM')
sni_params = run_model(sni_dir, 'SNI')

all_params = pd.concat([sham_params, sni_params], ignore_index=True)
all_params.to_csv("fitted_q_learning_parameters.csv", index=False)
print("Done. Parameters saved to 'fitted_q_learning_parameters.csv'")
