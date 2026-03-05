# -*- coding: utf-8 -*-
"""
Created on Thu Jul 31 14:02:21 2025

@author: meaghan.creed
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import minimize
from sklearn.metrics import accuracy_score, log_loss, roc_auc_score

# === CONFIGURATION ===
data_folder = r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Bandit\TrickyBandit\SNI' # Set your folder path here
block_size = 3
#sham_dir = r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Bandit\TrickyBandit\SHAM'
#sni_dir = r'C:\Users\meaghan.creed\Box\CreedLabBoxDrive\Jeremy\SNI_Dopamine_Paper\Figure1_SNIBehavior\FED_Bandit\TrickyBandit\SNI'

#%%
# === RL FUNCTIONS ===
def softmax(q_left, q_right, beta):
    exp_r = np.exp(beta * q_right)
    exp_l = np.exp(beta * q_left)
    return exp_r / (exp_r + exp_l)

def neg_log_likelihood(params, choices, rewards):
    gamma, delta_pos, delta_omission, beta = params
    q_left, q_right = 0.5, 0.5
    log_likelihood = 0

    for choice, reward in zip(choices, rewards):
        p_right = softmax(q_left, q_right, beta)
        p_choice = p_right if choice == 1 else 1 - p_right
        p_choice = max(p_choice, 1e-10)
        log_likelihood += np.log(p_choice)

        if choice == 1:
            q_right = gamma * q_right + (delta_pos if reward else delta_omission)
            q_left = gamma * q_left
        else:
            q_left = gamma * q_left + (delta_pos if reward else delta_omission)
            q_right = gamma * q_right

    return -log_likelihood

# === BATCH ANALYSIS ===
summary_metrics = []

for file in os.listdir(data_folder):
    print("Files in directory:")
    print(os.listdir(data_folder))

#    if not file.endswith(".csv"):
#        continue

    df = pd.read_csv(os.path.join(data_folder, file))
    print(f"\nProcessing file: {file}  |  Events: {df['Event'].value_counts().to_dict()}")
    df = df[df['Event'].isin(['Left', 'Right', 'Pellet'])].reset_index(drop=True)

    choices = []  # 0 = Left, 1 = Right
    rewards = []  # 1 = reward, 0 = omission

    last_choice = None
    for _, row in df.iterrows():
        if row['Event'] == 'Left':
            last_choice = 0
        elif row['Event'] == 'Right':
            last_choice = 1
        elif row['Event'] == 'Pellet' and last_choice is not None:
            choices.append(last_choice)
            rewards.append(1)
            last_choice = None
        elif row['Event'] in ['Left', 'Right']:
            choices.append(last_choice)
            rewards.append(0)

    choices = np.array(choices)
    rewards = np.array(rewards)

    # Fit the model
    bounds = [(0.01, 1.0), (0, 2), (-1, 1), (20.01, 300.0)]
    initial_params = [0.8, 0.5, -0.2, 150.0]
    result = minimize(neg_log_likelihood, x0=initial_params, args=(choices, rewards),
                      bounds=bounds, method='L-BFGS-B')

    gamma, delta_pos, delta_omission, beta = result.x

    # Predict trial-by-trial
    q_left, q_right = 0.5, 0.5
    predicted_probs = []
    predicted_choices = []

    for choice, reward in zip(choices, rewards):
        p_right = softmax(q_left, q_right, beta)
        predicted_probs.append(p_right)
        predicted_choices.append(int(p_right > 0.5))

        if choice == 1:
            q_right = gamma * q_right + (delta_pos if reward else delta_omission)
            q_left = gamma * q_left
        else:
            q_left = gamma * q_left + (delta_pos if reward else delta_omission)
            q_right = gamma * q_right

    predicted_choices = np.array(predicted_choices)
    predicted_probs = np.array(predicted_probs)

    # === MODEL EVALUATION ===
    accuracy = accuracy_score(choices, predicted_choices)
    log_likelihood = -neg_log_likelihood([gamma, delta_pos, delta_omission, beta], choices, rewards)
    aic = 2 * 4 - 2 * log_likelihood
    cross_entropy = log_loss(choices, predicted_probs)
    auc = roc_auc_score(choices, predicted_probs)

    summary_metrics.append({
        'Mouse': file,
        'Gamma': gamma,
        'Delta+': delta_pos,
        'Delta0': delta_omission,
        'Beta': beta,
        'Accuracy': accuracy,
        'LogLikelihood': log_likelihood,
        'AIC': aic,
        'CrossEntropy': cross_entropy,
        'ROC_AUC': auc
    })

    # === PLOTTING ===
    actual = choices
    predicted = predicted_probs
    n_blocks = len(actual) // block_size

    blocks = np.arange(n_blocks)
    mean_actual = [np.mean(actual[i*block_size:(i+1)*block_size]) for i in blocks]
    mean_predicted = [np.mean(predicted[i*block_size:(i+1)*block_size]) for i in blocks]
    reward_blocks = [np.any(rewards[i*block_size:(i+1)*block_size]) for i in blocks]

    plt.figure(figsize=(8, 4))
    for i, r in enumerate(reward_blocks):
        if r:
            plt.axvspan(i - 0.5, i + 0.5, color='lightgreen', alpha=0.3)
    plt.plot(blocks, mean_actual, label='Actual Choice (R=1)', marker='o')
    plt.plot(blocks, mean_predicted, label='Predicted P(Right)', marker='x')
    plt.xlabel('Trial Block (5 trials)')
    plt.ylabel('Probability / Mean Choice')
    plt.title(f"Mouse: {file}")
    plt.legend()
    plt.tight_layout()
    plt.show()

# === SAVE METRICS ===
pd.DataFrame(summary_metrics).to_csv("RL_model_fits_with_beta.csv", index=False)
