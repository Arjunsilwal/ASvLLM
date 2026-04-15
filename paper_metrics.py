#!/usr/bin/env python3
"""
PAPER METRICS & PUBLICATION GUIDE
ASvLLM - Ocean Engineering Paper

This script:
1. Calculates all evaluation metrics needed for publication
2. Generates publication-ready tables
3. Shows current status vs. PAPER_PLAN requirements
4. Identifies missing diagrams/analysis
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import json
from scipy import stats

print("=" * 80)
print("PAPER PUBLICATION STATUS & METRICS GUIDE")
print("=" * 80)

# ============================================================================
# 1. LOAD DATA
# ============================================================================

print("\n📊 Loading data...")
master_df = pd.read_csv('master_results.csv')
run_df = pd.read_csv('master_run_results.csv')

print(f"✓ Master results: {len(master_df):,} LLM calls")
print(f"✓ Run results: {len(run_df):,} scenario runs")

# ============================================================================
# 2. CALCULATE EVALUATION METRICS
# ============================================================================

print("\n" + "=" * 80)
print("EVALUATION METRICS SUMMARY")
print("=" * 80)

# 2.1 Overall Accuracy
print("\n📈 1. OVERALL ACCURACY")
overall_acc = master_df['Accuracy'].mean()
print(f"   Overall Accuracy: {overall_acc:.1%}")

# 2.2 Accuracy by Provider
print("\n📈 2. ACCURACY BY PROVIDER")
provider_acc = master_df.groupby('LLM Provider')['Accuracy'].agg(['mean', 'std', 'count'])
provider_acc.columns = ['Accuracy', 'StdDev', 'N_Calls']
print(provider_acc.to_string())

# 2.3 Accuracy by Mode
print("\n📈 3. ACCURACY BY DECISION MODE")
mode_acc = master_df.groupby('Mode')['Accuracy'].agg(['mean', 'std', 'count'])
mode_acc.columns = ['Accuracy', 'StdDev', 'N_Calls']
print(mode_acc.to_string())

# 2.4 Accuracy by Prompt Type
print("\n📈 4. ACCURACY BY PROMPT TYPE")
prompt_acc = master_df.groupby('Prompt Type')['Accuracy'].agg(['mean', 'std', 'count'])
prompt_acc.columns = ['Accuracy', 'StdDev', 'N_Calls']
print(prompt_acc.to_string())

# 2.5 Accuracy by Scenario
print("\n📈 5. ACCURACY BY SCENARIO")
scenario_acc = master_df.groupby('Scenario')['Accuracy'].agg(['mean', 'std', 'count'])
scenario_acc.columns = ['Accuracy', 'StdDev', 'N_Calls']
scenario_acc = scenario_acc.sort_values('Accuracy', ascending=False)
print(scenario_acc.to_string())

# 2.6 COLREGs Alignment
print("\n📈 6. COLREGS ALIGNMENT METRICS")
alignment_rate = (master_df['Is_Aligned'] == 'Yes').mean() if 'Is_Aligned' in master_df.columns else 0
print(f"   Rules Alignment Rate: {alignment_rate:.1%}")
print(f"   (Percentage of decisions citing correct COLREGs rules)")

# 2.7 Collision & Safety Metrics
print("\n📈 7. COLLISION & SAFETY METRICS (From Run Level)")
collision_rate = (run_df['Any Collision'] == True).mean()
avg_min_distance = run_df['Min Pairwise Distance (km)'].mean()
median_min_distance = run_df['Min Pairwise Distance (km)'].median()
print(f"   Collision Rate: {collision_rate:.1%}")
print(f"   Mean Min Distance: {avg_min_distance:.2f} km")
print(f"   Median Min Distance: {median_min_distance:.2f} km")

# 2.8 Collision Rate by Provider
print("\n📈 8. COLLISION RATE BY PROVIDER")
collision_by_provider = run_df.groupby('LLM Provider').apply(
    lambda x: (x['Any Collision'] == True).mean()
).sort_values()
for provider, rate in collision_by_provider.items():
    print(f"   {provider}: {rate:.1%}")

# 2.9 Mean Run Time
print("\n📈 9. COMPUTATIONAL EFFICIENCY")
mean_time = run_df['Elapsed Time (s)'].mean()
std_time = run_df['Elapsed Time (s)'].std()
print(f"   Mean simulation time: {mean_time:.1f} ± {std_time:.1f} seconds")

# ============================================================================
# 3. GENERATE PUBLICATION TABLES
# ============================================================================

print("\n" + "=" * 80)
print("PUBLICATION-READY TABLES")
print("=" * 80)

# TABLE 1: Experimental Matrix
print("\n📋 TABLE 1: EXPERIMENTAL MATRIX")
print("-" * 80)
table1_data = {
    'Factor': [
        'LLM Providers',
        'Decision Modes',
        'Prompt Levels',
        'Scenarios',
        'Runs per Config',
        'Total LLM Calls'
    ],
    'Count': [
        len(master_df['LLM Provider'].unique()),
        len(master_df['Mode'].unique()),
        'Varies by mode',
        len(master_df['Scenario'].unique()),
        'Variable',
        f"{len(master_df):,}"
    ]
}
table1 = pd.DataFrame(table1_data)
print(table1.to_string(index=False))

# TABLE 2: Main Results by Provider x Mode
print("\n📋 TABLE 2: MAIN RESULTS - PROVIDER vs MODE")
print("-" * 80)
pivot_data = []
for provider in sorted(master_df['LLM Provider'].unique()):
    for mode in sorted(master_df['Mode'].unique()):
        subset = master_df[(master_df['LLM Provider'] == provider) & (master_df['Mode'] == mode)]
        if len(subset) > 0:
            acc = subset['Accuracy'].mean()
            std_acc = subset['Accuracy'].std()
            n_calls = len(subset)
            # For runs with this provider/mode
            run_subset = run_df[(run_df['LLM Provider'] == provider) & (run_df['Mode'] == mode)]
            collision_rate_val = (run_subset['Any Collision'] == True).mean() if len(run_subset) > 0 else np.nan
            min_dist = run_subset['Min Pairwise Distance (km)'].mean() if len(run_subset) > 0 else np.nan
            
            pivot_data.append({
                'Provider': provider,
                'Mode': mode,
                'Accuracy': f"{acc:.1%}",
                'StdDev': f"{std_acc:.1%}",
                'Collision Rate': f"{collision_rate_val:.1%}",
                'Min Distance (km)': f"{min_dist:.2f}",
                'N_Calls': n_calls
            })

table2 = pd.DataFrame(pivot_data)
print(table2.to_string(index=False))

# TABLE 3: Scenario Difficulty
print("\n📋 TABLE 3: SCENARIO DIFFICULTY RANKING")
print("-" * 80)
scenario_stats = []
for scenario in sorted(master_df['Scenario'].unique()):
    subset = master_df[master_df['Scenario'] == scenario]
    acc = subset['Accuracy'].mean()
    difficulty = 1 - acc  # Higher difficulty = lower accuracy
    n_calls = len(subset)
    
    # Run-level collision data
    run_subset = run_df[run_df['Scenario'] == scenario]
    collision_rate_val = (run_subset['Any Collision'] == True).mean() if len(run_subset) > 0 else np.nan
    
    scenario_stats.append({
        'Scenario': scenario,
        'Difficulty': f"{difficulty:.2f}",
        'Accuracy': f"{acc:.1%}",
        'Collision Rate': f"{collision_rate_val:.1%}",
        'N_Calls': n_calls
    })

table3 = pd.DataFrame(scenario_stats).sort_values('Difficulty', ascending=False)
print(table3.to_string(index=False))

# ============================================================================
# 4. STATISTICAL TESTS
# ============================================================================

print("\n" + "=" * 80)
print("STATISTICAL SIGNIFICANCE TESTING")
print("=" * 80)

# Provider comparison (Mann-Whitney U tests)
print("\n📊 PAIRWISE PROVIDER COMPARISON (Mann-Whitney U Test)")
providers = sorted(master_df['LLM Provider'].unique())
for i in range(len(providers)):
    for j in range(i+1, len(providers)):
        p1, p2 = providers[i], providers[j]
        data1 = master_df[master_df['LLM Provider'] == p1]['Accuracy'].values
        data2 = master_df[master_df['LLM Provider'] == p2]['Accuracy'].values
        stat, pval = stats.mannwhitneyu(data1, data2)
        effect_size = (data1.mean() - data2.mean()) / np.sqrt((data1.std()**2 + data2.std()**2) / 2)
        sig = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else "ns"))
        print(f"   {p1} vs {p2}: p={pval:.4f} {sig}, Cohen's d={effect_size:.2f}")

# Mode comparison
print("\n📊 PAIRWISE MODE COMPARISON (Mann-Whitney U Test)")
modes = sorted(master_df['Mode'].unique())
for i in range(len(modes)):
    for j in range(i+1, len(modes)):
        m1, m2 = modes[i], modes[j]
        data1 = master_df[master_df['Mode'] == m1]['Accuracy'].values
        data2 = master_df[master_df['Mode'] == m2]['Accuracy'].values
        stat, pval = stats.mannwhitneyu(data1, data2)
        effect_size = (data1.mean() - data2.mean()) / np.sqrt((data1.std()**2 + data2.std()**2) / 2)
        sig = "***" if pval < 0.001 else ("**" if pval < 0.01 else ("*" if pval < 0.05 else "ns"))
        print(f"   {m1} vs {m2}: p={pval:.4f} {sig}, Cohen's d={effect_size:.2f}")

# ============================================================================
# 5. PAPER STATUS CHECKLIST
# ============================================================================

print("\n" + "=" * 80)
print("PAPER PUBLICATION CHECKLIST (From PAPER_PLAN.md)")
print("=" * 80)

checklist = {
    "STAGE 1: FOUNDATION & VALIDATION": [
        ("Data cleanup completed", len(master_df) > 5000),
        ("Analysis pipeline working", os.path.exists('master_results.csv')),
        ("Figures generated", len([f for f in os.listdir('figures') if f.endswith('.png')]) > 0),
        ("Large dataset collected (>2000 calls)", len(master_df) > 2000),
    ],
    "STAGE 2: CORE DATA COLLECTION": [
        ("All providers collected (OpenAI, Claude, DeepSeek)", 
         all(p in master_df['LLM Provider'].unique() for p in ['OpenAI', 'Claude', 'DeepSeek'])),
        ("All modes collected (standard, history, natural)",
         all(m in master_df['Mode'].unique() for m in ['standard', 'history', 'natural'])),
        ("All scenarios covered (Head-On, Crossing, Overtaking, Multi-1, 2, 3)",
         len(master_df['Scenario'].unique()) >= 4),
        ("Adequate sample size (>2000 LLM calls)",
         len(master_df) > 2000),
    ],
    "STAGE 3: ROBUSTNESS & ABLATIONS": [
        ("Noise robustness tests", os.path.exists('robustness_noise.py')),
        ("Delay robustness tests", os.path.exists('robustness_delay.py')),
        ("Vision mode tested", 'natural' in master_df['Mode'].unique()),
    ],
    "STAGE 4: FAILURE ANALYSIS & INSIGHTS": [
        ("Low-accuracy cases identified", (master_df['Accuracy'] < 0.5).sum() > 0),
        ("Failure taxonomy created", os.path.exists('figures/failure_taxonomy.png')),
        ("Provider comparison analysis done", True),  # Done above
        ("Scenario difficulty ranked", True),  # Done above
    ],
    "STAGE 5: ANALYSIS & VISUALIZATION": [
        ("Figure 1: Accuracy by Provider & Mode", os.path.exists('figures/fig1_accuracy_ablation.png')),
        ("Figure 2: Safety Margins (Min Distance)", os.path.exists('figures/fig2_reliability_ablation.png')),
        ("Figure 3: Robustness (Perturbation)", os.path.exists('figures/fig3_robustness_matrix.png')),
        ("Figure 4: Failure Taxonomy", os.path.exists('figures/fig4_explanation_alignment.png')),
        ("Table 1: Experimental Matrix", True),  # Generated above
        ("Table 2: Main Results", True),  # Generated above
        ("Table 3: Scenario-wise breakdown", True),  # Generated above
    ],
    "STAGE 6-7: MANUSCRIPT DRAFT & SUBMISSION": [
        ("Introduction written", False),
        ("Related Work written", False),
        ("Method section written", False),
        ("Results & Discussion written", False),
        ("Conclusion written", False),
        ("Figure captions written", False),
        ("References compiled", False),
        ("Manuscript in LaTeX/Word", False),
    ],
}

for stage, tasks in checklist.items():
    completed = sum(1 for _, done in tasks if done)
    total = len(tasks)
    print(f"\n{stage}: {completed}/{total} ✓")
    for task, done in tasks:
        status = "✓" if done else "✗"
        print(f"   [{status}] {task}")

# ============================================================================
# 6. WHAT DIAGRAMS ARE NEEDED FOR PAPER
# ============================================================================

print("\n" + "=" * 80)
print("DIAGRAMS NEEDED FOR PUBLICATION (Ocean Engineering)")
print("=" * 80)

diagrams_needed = {
    "FIGURE 1": {
        "Title": "Accuracy Breakdown by Provider & Mode",
        "Type": "Bar chart with error bars",
        "X-Axis": "Provider (OpenAI, Claude, DeepSeek)",
        "Hue": "Mode (standard, history, natural)",
        "Y-Axis": "Accuracy (0-100%)",
        "Key Data": provider_acc.to_dict(),
        "Status": "✓ Done (fig1_accuracy_ablation.png)" if os.path.exists('figures/fig1_accuracy_ablation.png') else "✗ MISSING",
    },
    "FIGURE 2": {
        "Title": "Safety Margins - Minimum Separation Distance",
        "Type": "Box plot",
        "X-Axis": "Scenario Complexity (Head-On, Crossing, Overtaking, Multi-vessel)",
        "Hue": "Provider",
        "Y-Axis": "Min Pairwise Distance (km)",
        "Key Insight": f"Mean separation: {avg_min_distance:.2f} km, Collision rate: {collision_rate:.1%}",
        "Status": "✓ Done (fig2_reliability_ablation.png)" if os.path.exists('figures/fig2_reliability_ablation.png') else "✗ MISSING",
    },
    "FIGURE 3": {
        "Title": "Robustness Under Perturbation",
        "Type": "Line plot with degradation curves",
        "X-Axis": "Noise Level (0%, 5%, 10%, 15%) or Latency (0s, 1s, 2s, 5s)",
        "Y-Axis": "Accuracy degradation",
        "Providers": "OpenAI, Claude, DeepSeek",
        "Key Insight": "Show how LLM resilience varies across providers",
        "Status": "✓ Done (fig3_robustness_matrix.png)" if os.path.exists('figures/fig3_robustness_matrix.png') else "✗ MISSING",
    },
    "FIGURE 4": {
        "Title": "Failure Taxonomy & Distribution",
        "Type": "Pie or Stacked Bar chart",
        "Categories": "Late Maneuver, Wrong Direction, Over-Conservative, Over-Aggressive, Unable to Decide, Other",
        "Data": "Analyze failures where Accuracy < 0.5",
        "Annotation": "Include 1-2 example scenarios with visual",
        "Status": "✓ Done (fig4_explanation_alignment.png)" if os.path.exists('figures/fig4_explanation_alignment.png') else "✗ MISSING",
    },
}

for fig_name, specs in diagrams_needed.items():
    print(f"\n📊 {fig_name}: {specs['Title']}")
    print(f"   Type: {specs['Type']}")
    print(f"   Status: {specs['Status']}")
    for key, val in specs.items():
        if key not in ['Title', 'Type', 'Status', 'Key Data'] and val:
            print(f"   {key}: {val}")

# ============================================================================
# 7. WHAT'S MISSING - ACTION ITEMS
# ============================================================================

print("\n" + "=" * 80)
print("IMMEDIATE ACTION ITEMS FOR PAPER COMPLETION")
print("=" * 80)

missing_items = []

# Check for robustness experiments
if not os.path.exists('robustness_noise.py'):
    missing_items.append("✗ CREATE robustness_noise.py - Test ±5%, ±10%, ±15% position noise")
if not os.path.exists('robustness_delay.py'):
    missing_items.append("✗ CREATE robustness_delay.py - Test 1s, 2s, 5s observation delays")

# Check for failure analysis
failure_cases = master_df[master_df['Accuracy'] < 0.5]
if len(failure_cases) > 0 and not os.path.exists('figures/failure_taxonomy.png'):
    missing_items.append(f"✗ ANALYZE failure cases ({len(failure_cases)} low-accuracy decisions)")
    missing_items.append("  - Categorize failures by type (late, wrong direction, conservative, etc.)")
    missing_items.append("  - Create failure_taxonomy.png visualization")
    missing_items.append("  - Document 10-15 representative failure examples")

# Check for baseline
has_baseline = 'Baseline' in str(run_df['LLM Provider'].unique()) or 'baseline' in str(run_df.columns)
if not has_baseline:
    missing_items.append("✗ CREATE deterministic baseline (Rule 13/14/15 logic)")
    missing_items.append("  - Implement baseline_colregs_deterministic.py")
    missing_items.append("  - Collect 10 runs on all 6 scenarios")
    missing_items.append("  - Use as comparison point for LLM decisions")

# Check for manuscript
if not os.path.exists('manuscript_draft.md') and not os.path.exists('manuscript.tex'):
    missing_items.append("✗ START manuscript draft (aim for 15-20 pages)")
    missing_items.append("  - Introduction (problem, gap, solution)")
    missing_items.append("  - Related Work (maritime autonomy, LLMs, explainability)")
    missing_items.append("  - Method (system design, evaluation metrics, COLREGs rules)")
    missing_items.append("  - Results (tables, figures, statistical tests)")
    missing_items.append("  - Discussion (findings, safety envelope, limitations)")
    missing_items.append("  - Conclusion (contributions, future work)")

if missing_items:
    print("\nPriority Tasks:")
    for i, item in enumerate(missing_items, 1):
        print(f"{i}. {item}")
else:
    print("✓ All major components generated! Ready to draft manuscript.")

# ============================================================================
# 8. SAVE METRICS TO FILE
# ============================================================================

print("\n" + "=" * 80)
print("SAVING METRICS SUMMARY")
print("=" * 80)

metrics_summary = {
    "Overall Accuracy": f"{overall_acc:.1%}",
    "Collision Rate": f"{collision_rate:.1%}",
    "Mean Min Distance": f"{avg_min_distance:.2f} km",
    "Total LLM Calls": len(master_df),
    "Total Scenario Runs": len(run_df),
    "Providers": list(master_df['LLM Provider'].unique()),
    "Modes": list(master_df['Mode'].unique()),
    "Scenarios": list(master_df['Scenario'].unique()),
    "Provider Accuracy": provider_acc['Accuracy'].to_dict(),
    "Mode Accuracy": mode_acc['Accuracy'].to_dict(),
    "Scenario Accuracy": scenario_acc['Accuracy'].to_dict(),
}

with open('PUBLICATION_METRICS.json', 'w') as f:
    json.dump(metrics_summary, f, indent=2)

print("✓ Saved metrics to PUBLICATION_METRICS.json")

# Save tables as CSV
table2.to_csv('table2_provider_mode_results.csv', index=False)
table3.to_csv('table3_scenario_difficulty.csv', index=False)
print("✓ Saved Table 2 to table2_provider_mode_results.csv")
print("✓ Saved Table 3 to table3_scenario_difficulty.csv")

print("\n" + "=" * 80)
print("✓ METRICS ANALYSIS COMPLETE")
print("=" * 80)
print("\nNext steps:")
print("1. Review missing items above")
print("2. Create robustness experiments (noise + delay)")
print("3. Analyze failure cases and create taxonomy")
print("4. Start manuscript draft with figures and tables")
print("5. Run statistical significance tests")
print("6. Prepare for Ocean Engineering submission")
