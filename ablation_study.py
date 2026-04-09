import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import os

from analysis_utils import add_analysis_columns
from analysis_config import (MODE_ORDER, PROVIDER_ORDER, SCENARIO_ORDER, 
                             PLOT_STYLE, FIG_SIZES)

# 1. LOAD DATA
df = pd.read_csv("master_results.csv")
os.makedirs("figures", exist_ok=True)

# Ensure analysis columns exist
if 'Is_Aligned' not in df.columns:
    df = add_analysis_columns(df)

# This script now focuses on complementary ablations (not duplicates of final_plots.py).
# final_plots.py keeps the 4 "main paper" summary figures.

sns.set_theme(style=PLOT_STYLE)

# --- ABLATION 1: PROMPT ENGINEERING (STANDARD MODE ONLY) ---
standard_df = df[df['Mode'] == 'standard'].copy()
prompt_order = [p for p in ['minimal', 'moderate', 'detailed', 'natural', 'tss']
                if p in standard_df['Prompt Type'].unique()]
plt.figure(figsize=(11, 6))
sns.barplot(
    data=standard_df,
    x='Prompt Type',
    y='Accuracy',
    hue='LLM Provider',
    order=prompt_order,
    hue_order=[p for p in PROVIDER_ORDER if p in standard_df['LLM Provider'].unique()],
    palette='Set2'
)
plt.title("Ablation 1: Prompt-Level Effect in Standard Mode")
plt.ylim(0, 1.05)
plt.ylabel("Mean Accuracy")
plt.xlabel("Prompt Type")
plt.tight_layout()
plt.savefig("figures/ablation_prompt_effect_standard_mode.png")

# --- ABLATION 2: MODE GAIN OVER STANDARD ---
mode_means = df.groupby(['LLM Provider', 'Mode'])['Accuracy'].mean().reset_index()
baseline = mode_means[mode_means['Mode'] == 'standard'][['LLM Provider', 'Accuracy']].rename(
    columns={'Accuracy': 'standard_acc'}
)
gain_df = mode_means.merge(baseline, on='LLM Provider', how='left')
gain_df['Accuracy_Gain_vs_Standard'] = gain_df['Accuracy'] - gain_df['standard_acc']
gain_df = gain_df[gain_df['Mode'] != 'standard']

plt.figure(figsize=(10, 6))
sns.barplot(
    data=gain_df,
    x='LLM Provider',
    y='Accuracy_Gain_vs_Standard',
    hue='Mode',
    hue_order=[m for m in MODE_ORDER if m != 'standard'],
    order=[p for p in PROVIDER_ORDER if p in gain_df['LLM Provider'].unique()],
    palette='coolwarm'
)
plt.axhline(0, color='black', linewidth=1)
plt.title("Ablation 2: Accuracy Gain vs Standard Mode")
plt.ylabel("Delta Accuracy")
plt.xlabel("LLM Provider")
plt.tight_layout()
plt.savefig("figures/ablation_mode_gain_vs_standard.png")

# --- ABLATION 3: SCENARIO FAILURE-RATE HEATMAP ---
failure_df = df.copy()
failure_df['Failure_Rate'] = 1.0 - failure_df['Accuracy']
scenario_avail = [s for s in scenario_order if s in failure_df['Scenario'].unique()]
pivot_fail = failure_df.groupby(['Scenario', 'Mode'])['Failure_Rate'].mean().unstack()
pivot_fail = pivot_fail.reindex(index=scenario_avail, columns=[m for m in mode_order if m in pivot_fail.columns])

plt.figure(figsize=(10, 5))
sns.heatmap(pivot_fail, annot=True, fmt=".2f", cmap="Reds")
plt.title("Ablation 3: Scenario Failure Rate by Mode")
plt.ylabel("Scenario")
plt.xlabel("Mode")
plt.tight_layout()
plt.savefig("figures/ablation_scenario_failure_heatmap.png")

# --- ABLATION 4: ALIGNMENT BY PROMPT (STANDARD MODE) ---
alignment_df = standard_df.groupby(['LLM Provider', 'Prompt Type'])['Is_Aligned'].mean().reset_index()
plt.figure(figsize=(11, 6))
sns.barplot(
    data=alignment_df,
    x='Prompt Type',
    y='Is_Aligned',
    hue='LLM Provider',
    order=prompt_order,
    hue_order=[p for p in provider_order if p in alignment_df['LLM Provider'].unique()],
    palette='rocket'
)
plt.title("Ablation 4: Rule-Alignment Rate by Prompt (Standard Mode)")
plt.ylim(0, 1.05)
plt.ylabel("Alignment Rate")
plt.xlabel("Prompt Type")
plt.tight_layout()
plt.savefig("figures/ablation_prompt_alignment_standard_mode.png")

print("Saved 4 complementary ablation figures under figures/.")