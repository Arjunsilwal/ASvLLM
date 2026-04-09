import pandas as pd
import glob
import os
import sys
import matplotlib.pyplot as plt
import seaborn as sns

from analysis_utils import add_analysis_columns, calculate_metrics, print_metrics
from analysis_config import PLOT_STYLE, PLOT_CONTEXT, FONT_SCALE

# 1. SETUP & DATA MERGING
print(f"Current Directory: {os.getcwd()}")
log_folder = 'logs'
all_files = glob.glob(os.path.join(log_folder, "results_*.csv"))
run_summary_path = os.path.join(log_folder, "run_summary.csv")

if not all_files:
    print("Error: No files found in 'logs/' folder. Re-run batch collection before analysis.")
    sys.exit(1)

print(f"Merging {len(all_files)} files...")
df = pd.concat([pd.read_csv(f) for f in all_files], ignore_index=True)

# 2. DATA PROCESSING
df = add_analysis_columns(df)
df.to_csv("master_results.csv", index=False)

run_df = None
if os.path.exists(run_summary_path):
    run_df = pd.read_csv(run_summary_path)
    run_df.to_csv("master_run_results.csv", index=False)
else:
    print("Warning: logs/run_summary.csv not found. Scenario-level metrics will be unavailable.")

# 3. GENERATE PLOTS
sns.set_theme(style=PLOT_STYLE, context=PLOT_CONTEXT, font_scale=FONT_SCALE)

# Plot 1: Accuracy by Provider and Mode
plt.figure(figsize=(10, 6))
sns.barplot(data=df, x='LLM Provider', y='Accuracy', hue='Mode', palette='viridis')
plt.title("Overall Compliance: Provider vs Mode")
plt.ylim(0, 1.1)
plt.savefig("eda_accuracy_by_mode.png")

# Plot 2: Scenario Difficulty
plt.figure(figsize=(12, 6))
sns.barplot(data=df, x='Scenario', y='Accuracy', hue='LLM Provider', palette='muted')
plt.xticks(rotation=45)
plt.title("Performance across Different Scenarios")
plt.tight_layout()
plt.savefig("eda_scenario_difficulty.png")

# 4. CALCULATE FINAL JOURNAL METRICS
metrics = calculate_metrics(df)
print_metrics(metrics, run_df)
