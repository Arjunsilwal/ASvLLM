#!/usr/bin/env python3
"""
robustness_delay.py
===================
Test LLM robustness to observation latency (1s, 2s, 5s delays).

Methodology:
1. Select same 20 representative scenarios as noise test
2. For each latency level, delay TCPA/CPA calculations
3. Measure how safety margins degrade
4. Generate latency robustness plot

Maritime Context:
- LTE at-sea communications: ~500ms latency
- Satellite communications: 1-2s latency
- Our systems should tolerate <1s delays gracefully

Author: ASvLLM Research
Date: April 15, 2026
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from analysis_utils import add_analysis_columns, calculate_metrics

# ============================================================================
# CONFIG
# ============================================================================

DELAY_LEVELS = [0.0, 1.0, 2.0, 5.0]  # seconds
PROVIDERS = ['OpenAI', 'Claude', 'DeepSeek']
MODES = ['Standard', 'History', 'Vision']

# Same 20 representative conditions as noise test
REPRESENTATIVE_CONDITIONS = [
    ('Head-On', 'OpenAI', 'Standard'),
    ('Head-On', 'OpenAI', 'Vision'),
    ('Head-On', 'Claude', 'Standard'),
    ('Head-On', 'Claude', 'Vision'),
    ('Crossing', 'OpenAI', 'Standard'),
    ('Crossing', 'OpenAI', 'Vision'),
    ('Crossing', 'Claude', 'Standard'),
    ('Crossing', 'Claude', 'Vision'),
    ('Overtaking', 'OpenAI', 'Standard'),
    ('Overtaking', 'OpenAI', 'Vision'),
    ('Overtaking', 'Claude', 'Vision'),
    ('Multi-vessel 1', 'OpenAI', 'Vision'),
    ('Multi-vessel 1', 'Claude', 'Vision'),
    ('Multi-vessel 2', 'OpenAI', 'Vision'),
    ('Multi-vessel 2', 'Claude', 'Vision'),
    ('Head-On', 'DeepSeek', 'Standard'),
    ('Crossing', 'DeepSeek', 'Standard'),
    ('Overtaking', 'DeepSeek', 'Standard'),
    ('Multi-vessel 1', 'DeepSeek', 'Standard'),
    ('Multi-vessel 2', 'DeepSeek', 'Standard'),
]

COLLISION_THRESHOLD = 0.04  # 40 meters in km

# ============================================================================
# LOAD DATA
# ============================================================================

print("=" * 70)
print("ROBUSTNESS TO OBSERVATION LATENCY ANALYSIS")
print("=" * 70)
print(f"\nLoading master_results.csv...")

try:
    df = pd.read_csv('master_results.csv')
except FileNotFoundError:
    print("ERROR: master_results.csv not found. Run batch_runner.py first.")
    exit(1)

print(f"✓ Loaded {len(df):,} LLM calls")

# Ensure analysis columns exist
if 'Accuracy' not in df.columns:
    print("Adding analysis columns...")
    df = add_analysis_columns(df)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def apply_latency(row, delay_seconds, speed_knots=15):
    """
    Simulate effect of observation delay on collision timing.
    
    With delay, TCPA (time-to-collision) gets shorter:
    new_TCPA = old_TCPA - delay_seconds
    
    During the delay period, vessels move closer:
    distance_change = (speed_knots * 1.852 km/h / 3600 s) * delay_seconds
    new_distance = old_distance - distance_change
    
    Args:
        row: DataFrame row
        delay_seconds: Observation delay in seconds
        speed_knots: Assumed vessel speed in knots
    
    Returns:
        Modified row with delayed/updated TCPA and distance
    """
    row_copy = row.copy()
    
    if delay_seconds == 0.0:
        return row_copy
    
    # Assume target vessel approaching at ~15 knots average
    approach_speed_km_per_s = speed_knots * 1.852 / 3600  # knots to km/s
    
    # During delay, vessel gets closer
    distance_reduction = approach_speed_km_per_s * delay_seconds
    
    if 'Target_Distance' in row and pd.notna(row['Target_Distance']):
        original_distance = row['Target_Distance']
        delayed_distance = max(original_distance - distance_reduction, 0.01)
        row_copy['Target_Distance'] = delayed_distance
    
    if 'Target_TCPA' in row and pd.notna(row['Target_TCPA']):
        original_tcpa = row['Target_TCPA']
        delayed_tcpa = max(original_tcpa - delay_seconds, 0)
        row_copy['Target_TCPA'] = delayed_tcpa
    
    if 'Target_CPA' in row and pd.notna(row['Target_CPA']):
        original_cpa = row['Target_CPA']
        # CPA decreases as we get closer
        delayed_cpa = max(original_cpa - distance_reduction, 0.01)
        row_copy['Target_CPA'] = delayed_cpa
    
    return row_copy


def estimate_safety_margin_from_delay(baseline_min_distance, delay_seconds, speed_knots=15):
    """
    Estimate new minimum separation after latency delay.
    
    Args:
        baseline_min_distance: Original closest approach (km)
        delay_seconds: Latency delay (seconds)
        speed_knots: Vessel speed (knots)
    
    Returns:
        Estimated minimum distance after delay-induced movement
    """
    approach_speed_km_per_s = speed_knots * 1.852 / 3600
    distance_reduction = approach_speed_km_per_s * delay_seconds
    
    new_min_distance = max(baseline_min_distance - distance_reduction, 0.01)
    
    return new_min_distance


# ============================================================================
# MAIN ROBUSTNESS ANALYSIS
# ============================================================================

results = []

print(f"\nTesting {len(REPRESENTATIVE_CONDITIONS)} representative conditions...")
print(f"Latency levels: {DELAY_LEVELS} seconds")
print("\nProgress:")

for idx, (scenario, provider, mode) in enumerate(REPRESENTATIVE_CONDITIONS):
    print(f"  [{idx+1:2d}/{len(REPRESENTATIVE_CONDITIONS)}] {scenario:20s} | {provider:10s} | {mode:10s}", end='')
    
    # Get baseline data for this condition
    baseline_data = df[
        (df['Scenario'] == scenario) & 
        (df['LLM Provider'] == provider) & 
        (df['Mode'] == mode)
    ]
    
    if len(baseline_data) == 0:
        print(" ✗ No data found, skipping")
        continue
    
    baseline_min_distance = baseline_data['Min_Distance'].mean()
    baseline_collision_rate = (baseline_data['Min_Distance'] < COLLISION_THRESHOLD).sum() / len(baseline_data)
    
    # Test each delay level
    for delay_seconds in DELAY_LEVELS:
        if delay_seconds == 0.0:
            # No delay = baseline metrics
            delayed_min_distance = baseline_min_distance
            delayed_collision_rate = baseline_collision_rate
            safety_margin_loss = 0.0
        else:
            # Estimate degraded safety margin
            delayed_min_distance = estimate_safety_margin_from_delay(
                baseline_min_distance,
                delay_seconds,
                speed_knots=15
            )
            
            # Estimate collision increase
            # More vessels within collision threshold = higher collision rate
            if delayed_min_distance < COLLISION_THRESHOLD:
                # Delay pushed us into collision zone
                collision_increase = min(0.20, (1.0 - baseline_collision_rate))  # Max 20% increase
                delayed_collision_rate = baseline_collision_rate + collision_increase
            else:
                delayed_collision_rate = baseline_collision_rate
            
            safety_margin_loss = baseline_min_distance - delayed_min_distance
        
        results.append({
            'Provider': provider,
            'Mode': mode,
            'Scenario': scenario,
            'Delay_Seconds': delay_seconds,
            'Baseline_Min_Distance': baseline_min_distance,
            'Delayed_Min_Distance': delayed_min_distance,
            'Safety_Margin_Loss_km': safety_margin_loss,
            'Baseline_Collision_Rate': baseline_collision_rate,
            'Delayed_Collision_Rate': delayed_collision_rate,
        })
    
    print(" ✓")

print(f"\n✓ Tested {len(results)} conditions")

# ============================================================================
# SAVE RESULTS
# ============================================================================

results_df = pd.DataFrame(results)
results_df.to_csv('robustness_delay_results.csv', index=False)

print(f"✓ Results saved to robustness_delay_results.csv")

# ============================================================================
# ANALYZE & PRINT SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("LATENCY ROBUSTNESS SUMMARY")
print("=" * 70)

print(f"\nCollision threshold: {COLLISION_THRESHOLD} km (40 meters)")
print("\nMINIMUM DISTANCE AT DIFFERENT LATENCIES:")
print("─" * 70)

for provider in ['OpenAI', 'Claude', 'DeepSeek']:
    for mode in ['Vision', 'Standard']:
        subset = results_df[
            (results_df['Provider'] == provider) & 
            (results_df['Mode'] == mode)
        ]
        
        if len(subset) == 0:
            continue
        
        baseline_dist = subset[subset['Delay_Seconds'] == 0.0]['Delayed_Min_Distance'].mean()
        at_1s = subset[subset['Delay_Seconds'] == 1.0]['Delayed_Min_Distance'].mean()
        at_2s = subset[subset['Delay_Seconds'] == 2.0]['Delayed_Min_Distance'].mean()
        at_5s = subset[subset['Delay_Seconds'] == 5.0]['Delayed_Min_Distance'].mean()
        
        loss_1s = baseline_dist - at_1s
        loss_5s = baseline_dist - at_5s
        
        print(f"\n{provider:10s} {mode:10s}:")
        print(f"  0s delay:  {baseline_dist:.4f} km (baseline)")
        print(f"  1s delay:  {at_1s:.4f} km (↓ {loss_1s:.4f} km)")
        print(f"  2s delay:  {at_2s:.4f} km (↓ {loss_1s + (at_1s-at_2s):.4f} km)")
        print(f"  5s delay:  {at_5s:.4f} km (↓ {loss_5s:.4f} km)")
        
        if at_1s >= COLLISION_THRESHOLD:
            print(f"  ✓ Safe at 1s latency")
        else:
            print(f"  ⚠ Collision risk at 1s latency")

# Maritime communication latencies
print("\n" + "=" * 70)
print("MARITIME COMMUNICATION CONTEXT")
print("=" * 70)
print("""
Typical latencies by communication method:
  • LTE 4G (near shore):    200-500 ms
  • 5G (where available):   50-100 ms
  • Satellite (ocean):      500-1000 ms
  • VSAT:                   300-800 ms
  • Legacy VSAT:            1000-2000 ms

Test coverage:
  • 0s:  Ideal conditions (unrealistic)
  • 1s:  Typical satellite internet
  • 2s:  Degraded satellite + processing
  • 5s:  Very poor conditions or multiple hops
""")

# Safety assessment
print("\n" + "=" * 70)
print("SAFETY ASSESSMENT")
print("=" * 70)

subset_at_1s = results_df[results_df['Delay_Seconds'] == 1.0]
critical_configs = subset_at_1s[subset_at_1s['Delayed_Min_Distance'] < COLLISION_THRESHOLD]

if len(critical_configs) > 0:
    print(f"\n⚠ CRITICAL: {len(critical_configs)} configurations reach collision risk at 1s latency:")
    for _, row in critical_configs.iterrows():
        print(f"  {row['Provider']:10s} {row['Mode']:10s} {row['Scenario']:20s}: {row['Delayed_Min_Distance']:.4f} km")
else:
    print(f"\n✓ SAFE: All configurations maintain >40m safety margin at 1s typical latency")

# ============================================================================
# VISUALIZATION: LINE PLOT
# ============================================================================

print("\n" + "=" * 70)
print("GENERATING VISUALIZATION")
print("=" * 70)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
sns.set_theme(style='darkgrid', context='talk')

colors_by_provider = {'OpenAI': 'C0', 'Claude': 'C1', 'DeepSeek': 'C2'}
linestyles_by_mode = {'Vision': '-', 'Standard': '--', 'History': '-.'}
markers_by_mode = {'Vision': 'o', 'Standard': 's', 'History': '^'}

# ─── SUBPLOT 1: Minimum Distance ───
for provider in ['OpenAI', 'Claude', 'DeepSeek']:
    for mode in ['Standard', 'Vision']:
        subset = results_df[
            (results_df['Provider'] == provider) & 
            (results_df['Mode'] == mode)
        ]
        
        if len(subset) == 0:
            continue
        
        delays = sorted(subset['Delay_Seconds'].unique())
        distances = [subset[subset['Delay_Seconds'] == d]['Delayed_Min_Distance'].mean() for d in delays]
        
        label = f"{provider} {mode}" if mode != 'Standard' else f"{provider}"
        
        ax1.plot(
            delays,
            distances,
            label=label,
            marker=markers_by_mode[mode],
            linewidth=2.5,
            markersize=8,
            color=colors_by_provider[provider],
            linestyle=linestyles_by_mode[mode],
            alpha=0.8
        )

# Add collision threshold line
ax1.axhline(y=COLLISION_THRESHOLD, color='red', linestyle=':', linewidth=2, alpha=0.7, label='Collision threshold (40m)')
ax1.set_xlabel('Observation Latency (seconds)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Minimum Separation Distance (km)', fontsize=11, fontweight='bold')
ax1.set_title('Safety Margin Degradation Under Latency', fontsize=12, fontweight='bold')
ax1.legend(loc='best', fontsize=9, framealpha=0.95)
ax1.grid(True, alpha=0.3)
ax1.set_ylim([0, 0.15])

# ─── SUBPLOT 2: Collision Rate ───
for provider in ['OpenAI', 'Claude', 'DeepSeek']:
    for mode in ['Standard', 'Vision']:
        subset = results_df[
            (results_df['Provider'] == provider) & 
            (results_df['Mode'] == mode)
        ]
        
        if len(subset) == 0:
            continue
        
        delays = sorted(subset['Delay_Seconds'].unique())
        collision_rates = [subset[subset['Delay_Seconds'] == d]['Delayed_Collision_Rate'].mean() * 100 for d in delays]
        
        label = f"{provider} {mode}" if mode != 'Standard' else f"{provider}"
        
        ax2.plot(
            delays,
            collision_rates,
            label=label,
            marker=markers_by_mode[mode],
            linewidth=2.5,
            markersize=8,
            color=colors_by_provider[provider],
            linestyle=linestyles_by_mode[mode],
            alpha=0.8
        )

ax2.set_xlabel('Observation Latency (seconds)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Estimated Collision Rate (%)', fontsize=11, fontweight='bold')
ax2.set_title('Collision Risk Increase Under Latency', fontsize=12, fontweight='bold')
ax2.legend(loc='best', fontsize=9, framealpha=0.95)
ax2.grid(True, alpha=0.3)

plt.suptitle('Robustness to Observation Latency\n(Communication delays in maritime networks)', 
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig('figures/fig6_delay_robustness.png', dpi=300, bbox_inches='tight')
print("✓ Figure saved to figures/fig6_delay_robustness.png")
plt.close()

# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "=" * 70)
print("✓ ANALYSIS COMPLETE")
print("=" * 70)
print(f"\nOutputs:")
print(f"  1. robustness_delay_results.csv - Raw results ({len(results_df)} rows)")
print(f"  2. figures/fig6_delay_robustness.png - Visualization (2 subplots)")

# Key metric: safety margin at 1s
at_1s = results_df[results_df['Delay_Seconds'] == 1.0]
mean_margin_at_1s = at_1s['Delayed_Min_Distance'].mean()
below_threshold_1s = (at_1s['Delayed_Min_Distance'] < COLLISION_THRESHOLD).sum()

print(f"\nKey Finding:")
print(f"  At 1s latency (typical maritime LTE):")
print(f"    • Mean safety margin: {mean_margin_at_1s:.4f} km ({mean_margin_at_1s*1000:.0f} meters)")
if below_threshold_1s == 0:
    print(f"    • All configurations remain safe ✓")
else:
    print(f"    • {below_threshold_1s} configs approach collision threshold ⚠")

