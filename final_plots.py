import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

from analysis_utils import add_analysis_columns
from analysis_config import (PLOT_STYLE, PLOT_CONTEXT, FONT_SCALE, 
                             SIMPLE_SCENARIOS, COMPLEX_SCENARIOS, FIG_SIZES)

# 1. LOAD MASTER DATA
try:
    df = pd.read_csv("master_results.csv")
except FileNotFoundError:
    print("Error: master_results.csv not found. Run master_analysis.py first.")
    exit()

# Ensure analysis columns exist
if 'Accuracy' not in df.columns:
    df = add_analysis_columns(df)

# Set professional plotting style
sns.set_theme(style=PLOT_STYLE, context=PLOT_CONTEXT, font_scale=FONT_SCALE)
os.makedirs("figures", exist_ok=True)

# Define Scenario Complexity
df['Complexity'] = df['Scenario'].apply(lambda x: 'Simple' if x in SIMPLE_SCENARIOS else 'Complex')

# --- FIGURE 1: ACCURACY ABLATION (Mode vs. Provider) ---
plt.figure(figsize=(10, 6))
sns.barplot(data=df, x='LLM Provider', y='Accuracy', hue='Mode', palette='viridis')
plt.title("Figure 1: Accuracy Ablation - Impact of Intelligence Mode on Compliance")
plt.ylabel("Mean Accuracy (Compliance Rate)")
plt.ylim(0, 1.1)
plt.savefig("figures/fig1_accuracy_ablation.png")

# --- FIGURE 2: RELIABILITY ABLATION (Consistency Check) ---
# Calculate StdDev across 10 repeated runs
reliability_df = df.groupby(['LLM Provider', 'Mode', 'Scenario', 'Prompt Type'])['Accuracy'].std().reset_index()
plt.figure(figsize=(10, 6))
sns.barplot(data=reliability_df, x='LLM Provider', y='Accuracy', hue='Mode', palette='magma')
plt.title("Figure 2: Reliability Ablation - Decision Consistency (Lower is Better)")
plt.ylabel("Avg Standard Deviation (Stochasticity)")
plt.savefig("figures/fig2_reliability_ablation.png")

# --- FIGURE 3: ROBUSTNESS MATRIX (Complexity Tolerance) ---
plt.figure(figsize=(10, 6))
sns.barplot(data=df, x='LLM Provider', y='Accuracy', hue='Complexity', palette='coolwarm')
plt.title("Figure 3: Robustness Analysis - Simple vs. Complex Scenario Performance")
plt.ylabel("Compliance Rate")
plt.savefig("figures/fig3_robustness_matrix.png")

# --- FIGURE 4: EXPLANATION ALIGNMENT (The Novelty Contribution) ---
# Plot % of successful runs where the logic (rule citation) was also correct
plt.figure(figsize=(10, 6))
alignment_df = df[df['Accuracy'] == 1.0] # Only look at Pass verdicts
sns.barplot(data=alignment_df, x='LLM Provider', y='Is_Aligned', hue='Mode', palette='rocket')
plt.title("Figure 4: Explanation Reasoning - Rule Alignment in Successful Maneuvers")
plt.ylabel("Alignment Rate (Correct Action + Correct Rule)")
plt.savefig("figures/fig4_explanation_alignment.png")

print("All 4 Journal Figures have been saved in the 'figures/' folder.")