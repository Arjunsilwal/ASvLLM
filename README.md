# ASvLLM: LLM-Driven COLREGs-Compliant Collision Avoidance for Autonomous Vessels

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![DOI](https://img.shields.io/badge/DOI-10.1016%2Fxxxx-blueviolet)](https://doi.org/10.1016/xxxx)

**ASvLLM** is a research benchmark for evaluating Large Language Models (LLMs) as decision makers in autonomous maritime collision avoidance. Built with Pygame, it simulates realistic multi-vessel encounters and queries LLMs (OpenAI, Claude, DeepSeek) to generate COLREGs-compliant navigation decisions.

> 🎯 **Research Focus**: Can LLMs serve as interpretable, rule-grounded tactical planners for safety-critical maritime autonomy? How do decision modes, prompt engineering, and provider choice affect safety and compliance?

## 📖 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Experimental Design](#experimental-design)
- [Research Questions](#research-questions)
- [Project Architecture](#project-architecture)
- [Usage Guide](#usage-guide)
- [Analysis Pipeline](#analysis-pipeline)
- [Results & Outputs](#results--outputs)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)

---

## Overview

### The Problem

Maritime collision avoidance is a **safety-critical task** governed by international rules (COLREGs). Current approaches fall into two categories:

- **Rule-based systems**: Rigid, inflexible, but explainable and deterministic
- **Black-box ML/RL**: Adaptive but lack explainability and formal guarantees

**ASvLLM** investigates a middle ground: **Can LLMs reliably execute COLREGs rules while adapting to complex scenarios?**

### The Solution

ASvLLM benchmarks LLM decision-making across:

1. **Three decision modes** (varying complexity/memory):
   - `standard`: text-only state information
   - `prompt_history`: temporal memory (3-5 previous timesteps)
   - `natural`: vision-assisted (image + narrative context)

2. **Three major LLM providers** (OpenAI, Claude, DeepSeek):
   - Isolate model-specific behavior and robustness
   - Compare inference cost, latency, safety margins

3. **Six maritime scenarios** (simple → complex):
   - Head-on, crossing, overtaking, multi-vessel encounters
   - Traffic separation schemes (Rule 10)

4. **Quantified safety evaluation**:
   - Collision rates, DCPA (distance to closest point of approach)
   - COLREGs compliance accuracy (does action match rule?)
   - Rule alignment (does citation match action?)
   - Robustness under noise/delays

## Key Features

✅ **Realistic Simulator**
- Multi-vessel maritime physics with heading/speed control
- Collision detection and DCPA/TCPA prediction
- Real-time maneuver execution and logging

✅ **LLM Integration Framework**
- Support for OpenAI, Anthropic Claude, DeepSeek
- Async prompt/response pipeline (non-blocking)
- JSON schema validation for structured outputs
- Comprehensive error handling and retries

✅ **Flexible Decision Modes**
- Text-only with 5 prompt abstraction levels (minimal → detailed)
- Temporal memory with configurable history length
- Vision-assisted mode with scene capture and narrative context

✅ **Research-Grade Evaluation**
- Per-call decision logs (action, rule, confidence, latency)
- Scenario-level outcomes (collisions, separations, time-to-goal)
- Automated analysis pipeline (metrics, figures, statistical tests)
- 95% confidence intervals and effect size reporting

✅ **Reproducibility**
- All prompts, scenarios, and results logged
- Deterministic seeding available
- GitHub-ready codebase with clear separation of concerns

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Conda (recommended) or venv
- At least one LLM API key:
  - **OpenAI**: [Get API Key](https://platform.openai.com/api-keys)
  - **Anthropic Claude**: [Get API Key](https://console.anthropic.com)
  - **DeepSeek**: [Get API Key](https://platform.deepseek.com)

### Step 1: Clone Repository

```bash
git clone https://github.com/Arjunsilwal/ASvLLM.git
cd ASvLLM
```

### Step 2: Create Environment

**Using Conda (Recommended)**:
```bash
conda env create -f environment.yml
conda activate ASvLLM
```

**Using venv**:
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install --upgrade pip
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install pygame langchain-openai langchain-anthropic langchain-core \
            pandas seaborn matplotlib pandas numpy
```

### Step 4: Configure API Keys

Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY="sk-..."
CLAUDE_API_KEY="sk-ant-..."
DEEPSEEK_API_KEY="sk-..."
```

**Or set environment variables**:
```bash
export OPENAI_API_KEY="sk-..."
export CLAUDE_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="sk-..."
```

### Verify Installation

```bash
python -c "from env_utils import load_project_env; load_project_env(); print('✓ Setup OK')"
```

---

## Quick Start

### Interactive Simulation

```bash
python main.py
```

The Pygame window will open with a navigation toolbar. Select:
- **Mode**: `standard`, `prompt_history`, or `natural`
- **Provider**: `openai`, `claude`, or `deepseek`
- **Scenario**: Choose from 6 predefined encounters
- **Prompt Type**: `minimal`, `moderate`, `detailed`, `natural`, or `tss`

Click **LOAD** to begin. The LLM will receive vessel state and return navigation decisions in real time.

### Batch Experiments

Run 10 trials across all configurations (2-3 weeks of computation):

```bash
# Single provider
python batch_runner.py openai
python batch_runner.py claude

# All providers in sequence
python batch_runner.py all
```

**Optional**: Clear old results first:
```bash
python clear_data.py  # WARNING: Deletes logs/
```

### Single Quick Test

Run 5 scenarios to validate setup:
```bash
python validate_logs.py  # Checks data integrity
python master_analysis.py  # Processes current logs (if any)
```

---

## Experimental Design

### Research Questions

| ID | Question | Key Variables | Metric |
|----|----------|---------------|--------|
| **RQ1** | Which decision mode is most reliable across complexity? | Mode, Scenario | COLREGs Accuracy, StdDev |
| **RQ2** | How do prompt levels affect safety? | Prompt Type (standard mode) | Accuracy, min DCPA |
| **RQ3** | Which provider is most robust? | Provider | Accuracy, cost, latency |
| **RQ4** | What are failure modes under perturbations? | Noise, Delay | Robustness degradation |

### Experimental Matrix

| Factor | Levels | Notes |
|--------|--------|-------|
| **Mode** | standard, prompt_history, natural | DeepSeek excludes natural mode |
| **Provider** | openai, claude, deepseek | ~$0.5 per scenario |
| **Prompt** | minimal, moderate, detailed, natural, tss | Mode-specific (see config) |
| **Scenario** | 6 encounters | Head-on, crossing, overtaking, multi-vessel |
| **Runs per Config** | 10 | For consistency metrics (StdDev) |

**Expected Data**: ~2,500 LLM calls → ~960 scenario runs → $480-800 in API costs

### Metrics

| Category | Metric | Definition |
|----------|--------|-----------|
| **Safety** | Collision Rate | % of runs with collision |
| | Min DCPA (km) | Closest approach distance |
| | Goal Success | % vessels reaching destination |
| **Compliance** | COLREGs Accuracy | % of actions matching ground truth rule |
| | Rule Alignment | % where cited rule matches action |
| **Efficiency** | Time-to-Goal (s) | Scenario completion time |
| **Robustness** | Accuracy Drop (noise) | Degradation under ±5/10/15% perturbations |

---

## Research Questions & Hypotheses

### RQ1: Decision Mode Comparison

**Hypothesis**: `natural` > `prompt_history` ≥ `standard` in complex scenarios

- Does vision (image + text) improve accuracy in ambiguous encounters?
- Does temporal memory stabilize decisions under uncertainty?

**Expected findings**: Simple scenarios show minimal improvement; complex scenarios benefit from memory/vision.

### RQ2: Prompt Engineering

**Hypothesis**: `detailed` > `moderate` > `minimal` (diminishing returns past `detailed`)

- Higher tokens → better understanding of collision geometry?
- Narrative prompts (`natural`) engage better reasoning?

**Expected findings**: Accuracy plateau at ~200-300 tokens; over-prompting increases latency without gain.

### RQ3: Provider Robustness

**Hypothesis**: GPT-4 ≈ Claude > DeepSeek in complex scenarios

- Closed-model systems (OpenAI, Anthropic) vs. open-weight (DeepSeek)?
- Cost-benefit trade-off between accuracy and inference cost?

**Expected findings**: Marginal differences; all providers achieve >80% on simple scenarios.

### RQ4: Failure Modes

**Hypothesis**: LLMs fail under late detection, multi-party coordination, high-speed dynamics

- Where does LLM reasoning break down?
- What perturbations degrade performance most?

**Expected findings**: Noise (±10%) ↓ accuracy ~5-10%; Long delays (5s) ↓ accuracy ~15-20%.

---

## Project Architecture

### High-Level Flow

```
User Input (Mode/Provider/Scenario)
    ↓
GameManager loads EntityManager
    ↓
Scenario spawns vessels
    ↓
[Simulation Loop - 60 FPS]
  ├─ Update vessel position & heading
  ├─ Detect collision candidates (DCPA check)
  ├─ Package vessel context
  └─ [If conflict detected]
      ├─ Prompt builder → JSON prompt
      ├─ LLM API call (async)
      ├─ Response parser → Maneuver enum
      ├─ Vessel.set_maneuver()
      └─ Log decision + outcome
    ↓
Simulation ends (all reach goal OR timeout)
    ↓
Batch runner repeats for 10 runs
    ↓
[Post-Processing]
  ├─ master_analysis.py → CSV merge + metrics
  ├─ ablation_study.py → Supplementary figures
  ├─ mode_prompt_study.py → Interaction heatmaps
  └─ final_plots.py → Publication figures
```

### Core Modules

| File | Purpose | Key Classes |
|------|---------|-------------|
| `entity.py` | Vessel dynamics, heading control | `Vessel`, `Francisco` |
| `scenario_generator.py` | Predefined encounters | `head_on_scenario()`, `cross_over_scenario()`, etc. |
| `entity_manager_*.py` | LLM decision loops | `EntityManager` (3 variants) |
| `llm_text_manager.py` | Text-only LLM API | `LLMTextManager` |
| `llm_vision_manager.py` | Vision-capable LLM API | `LLMVisionManager` |
| `response_parser.py` | JSON → Maneuver mapping | `parse_llm_response_for_all()`, `Maneuver` enum |
| `batch_runner.py` | Experiment automation | `run_batch()`, `run_simulation_step()` |
| `master_analysis.py` | Data aggregation + metrics | CSV merge, compliance/reliability calculation |
| `analysis_utils.py` | Shared analysis functions | `extract_rule_num()`, `calculate_metrics()` |
| `analysis_config.py` | Constants & configuration | Orders, palettes, expected outputs |

---

## Usage Guide

### 1. Interactive Mode

Run a single scenario with visual feedback:

```bash
python main.py
```

**Controls**:
- Dropdown menus to select mode, provider, scenario, prompt
- Click **LOAD** to start simulation
- Watch vessels navigate in real time
- Click **PAUSE**/**RESUME** to control simulation
- Logs saved automatically to `logs/`

### 2. Batch Experiments

Automate repeated trials across all configurations:

```bash
# Run 10 trials × 6 scenarios × 5 prompt levels × 1 mode × 1 provider
python batch_runner.py openai

# Expected output:
# - logs/results_standard_openai.csv (LLM call logs)
# - logs/run_summary.csv (scenario-level outcomes)
# Total: ~300 rows per provider
```

### 3. Data Validation

Check data quality after collection:

```bash
python validate_logs.py

# Output:
# ✓ Loaded logs/results_standard_openai.csv: X rows
# ✓ All accuracy values in valid range [0.0, 1.0]
# ✓ All LLM responses contain valid JSON
# Summary: All checks PASSED
```

### 4. Custom Scenario

Extend `scenario_generator.py` with new encounter types:

```python
def custom_scenario(manager, sw, sh):
    """Define your custom multi-vessel encounter."""
    manager.vessels.clear()
    v1 = Vessel(100, sh//2, manager.pixels_per_km)
    v1.heading = math.pi/2  # East
    v1.speed = v1.max_speed
    v1.goal = [sw-100, sh//2]
    manager.add_vessel(v1)
    # ... more vessels
```

---

## Analysis Pipeline

After collecting experimental data (`logs/results_*.csv`):

### Step 1: Merge & Process

```bash
python master_analysis.py
```

**Output**:
- `master_results.csv` - Unified LLM call log + calculated fields
- `master_run_results.csv` - Scenario-level summary
- `eda_*.png` - Exploratory plots

**Metrics printed**:
- Compliance Rate (COLREGs accuracy)
- Reliability (decision consistency)
- Robustness Gap (simple vs. complex scenarios)
- Rule Alignment Rate

### Step 2: Generate Figures

```bash
# Core publication figures (4 figures)
python final_plots.py
# Output: figures/fig1_*.png, fig2_*.png, fig3_*.png, fig4_*.png

# Supplementary ablations (4 figures)
python ablation_study.py
# Output: figures/ablation_*.png

# Interaction analysis (3 heatmaps)
python mode_prompt_study.py
# Output: study_results/interaction_*.png
```

### Step 3: Full Pipeline (Automated)

```bash
# Run all analysis scripts in sequence
python run_all_analysis.py

# Verifies all expected outputs exist
# Exit code 0: SUCCESS
# Exit code 1: Missing outputs (check console for details)
```

---

## Results & Outputs

### Logs Structure

```
logs/
├── results_standard_openai.csv    # LLM calls: standard mode, OpenAI
├── results_prompt_history_openai.csv
├── results_natural_openai.csv     # (DeepSeek may be empty)
├── results_standard_claude.csv
├── ...
└── run_summary.csv               # Scenario-level: collisions, times, etc.
```

### CSV Columns

**`results_*.csv`** (one row per LLM call):
- `Experiment ID`, `Call ID` - Tracking
- `Scenario`, `Mode`, `Prompt Type` - Configuration
- `Involved Vessels` - Which vessels in conflict
- `Ground Truth (Prompt)` - Expected rule
- `LLM Action` - What model decided
- `LLM Cited Rule` - Rule reference from model
- `Verdict` - "Pass" or "Fail" (matches GT)
- `llm_response_json` - Full response for audit

**`run_summary.csv`** (one row per scenario run):
- `LLM Provider`, `Mode`, `Scenario`, `Run Number`
- `All Reached Goal` - Boolean
- `Any Collision` - Boolean
- `Min Pairwise Distance (km)` - Closest approach
- `LLM Calls` - Number of queries used

### Figures Generated

| Figure | Purpose | File |
|--------|---------|------|
| **Fig 1** | Accuracy by Provider & Mode | `fig1_accuracy_ablation.png` |
| **Fig 2** | Decision Consistency (StdDev) | `fig2_reliability_ablation.png` |
| **Fig 3** | Robustness (Simple vs. Complex) | `fig3_robustness_matrix.png` |
| **Fig 4** | Rule Alignment (Explainability) | `fig4_explanation_alignment.png` |
| **Ablation 1** | Prompt Engineering (standard mode) | `ablation_prompt_effect_standard_mode.png` |
| **Ablation 2** | Mode Improvement over baseline | `ablation_mode_gain_vs_standard.png` |
| **Ablation 3** | Scenario Failure Heatmap | `ablation_scenario_failure_heatmap.png` |
| **Ablation 4** | Rule Alignment by Prompt | `ablation_prompt_alignment_standard_mode.png` |

---

## Configuration

### Edit Decision Modes

In `batch_runner.py`:
```python
get_mode_prompt_matrix(target_llm):
    matrix = {
        "standard": ["minimal", "moderate", "detailed", "natural"],
        "prompt_history": ["natural"],
        "natural": ["natural"]
    }
    if target_llm == "deepseek":
        matrix.pop("natural", None)  # DeepSeek fallback
    return matrix
```

### Edit Simulation Parameters

In `entity_manager_standard.py`:
```python
self.llm_cooldown_duration = 5.0  # Min time between LLM calls
self.radar_range_km = 0.8         # Collision detection radius
self.pixels_per_km = 1000.0       # Scale factor
self.llm_call_count = 0           # Tracking
```

### Edit Scenarios

In `scenario_generator.py`, modify existing scenarios or add new ones:
```python
def head_on_scenario(manager, sw, sh):
    # Modify starting positions, speeds, goals
    pass
```

### Edit Analysis Config

In `analysis_config.py`:
```python
MODE_ORDER = ['standard', 'prompt_history', 'natural']
PROVIDER_ORDER = ['openai', 'claude', 'deepseek']
PLOT_STYLE = "whitegrid"
# ... update palettes, directories, etc.
```

---

## Troubleshooting

### Issue: "OPENAI_API_KEY not found"

**Solution**:
1. Check `.env` file exists in project root
2. Verify format: `OPENAI_API_KEY="sk-..."`
3. If using shell export: `echo $OPENAI_API_KEY` should not be empty
4. Restart terminal after setting env vars

### Issue: "Error: Failed to decode JSON response"

**Solution**:
- This is usually a prompt encoding error (smart quotes, accents)
- `llm_text_manager.py` has ASCII fallback; check for non-ASCII chars
- Update prompt templates in `prompts_generator/`

### Issue: Pygame window won't display

**Solution**:
- If running headless (no display): batch mode works fine (`batch_runner.py`)
- On Linux: `export SDL_VIDEODRIVER=dummy` (headless)
- On WSL2: Configure X11 forwarding

### Issue: LLM API rate limits

**Solution**:
- Add delay between calls in `batch_runner.py`:
  ```python
  time.sleep(1)  # Between LLM queries
  ```
- Lower `RUNS_PER_CONFIG` from 10 to 5
- Or use lower-tier models (Claude 3 Haiku, GPT-3.5)

### Issue: "master_results.csv not found"

**Solution**:
- Run `master_analysis.py` first to merge `logs/*.csv`
- Ensure `logs/results_*.csv` files exist
- Check logs folder: `ls logs/`

---

## Limitations

### Simulator

- **Simplified dynamics**: Constant speed; no wind, current, or wave effects
- **Deterministic timing**: Discrete timesteps (not continuous)
- **Limited collision physics**: Binary collision check (no partial contact)
- **2D only**: No depth/3D vessel maneuvering

### LLM Integration

- **Prompt engineering sensitivity**: Performance varies significantly with phrasing
- **Latency variable**: LLM response time 0.5-5s; real maritime decisions need <1s
- **Cost constraint**: Full experiment: $500-800 API costs
- **Model availability**: DeepSeek sometimes has limited capacity

### Evaluation

- **Limited scenarios**: 6 encounter types; real maritime encounters much more diverse
- **No human feedback**: LLM decisions not validated by maritime experts
- **Simplified rules**: COLREGs simplified to 5 major rules (real: 72 rules)
- **No long-term memory**: Context window limited; multi-hour scenarios impossible

### Generalization

- **Simulator-specific**: Results may not transfer to real vessels
- **Specific LLM versions**: Results tied to model snapshot (April 2026)
- **English-only**: Prompts in English; multilingual evaluation needed

---

## Contributing

We welcome contributions! To add features, fix bugs, or improve documentation:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feat/my-feature`
3. **Make changes** with clear commit messages
4. **Test** your changes: `python validate_logs.py`
5. **Submit** a pull request with description

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ASvLLM.git
cd ASvLLM

# Create dev branch
git checkout -b dev

# Install dev dependencies (if any)
pip install black pytest

# Format code
black *.py
```

### Code Standards

- Follow [PEP 8](https://pep8.org/) (enforced via Black)
- Add docstrings to new functions
- Test with `validate_logs.py` before submitting

---

## Citation

To cite this project in your research:

```bibtex
@article{asvllm2026,
  title={LLM-Driven COLREGs-Compliant Decision Making for Autonomous Surface Vessel Collision Avoidance},
  author={Silwal, Arjun},
  journal={Ocean Engineering},
  year={2026},
  doi={10.1016/xxxx}
}
```

### Related Work

- [International Regulations for Preventing Collisions at Sea (COLREGs)](https://www.imo.org/en/About/Conventions/Pages/COLREG.aspx)
- [Maritime Autonomy & Collision Avoidance](https://www.dnvgl.com/)
- [LLM Decision-Making for Robotics](https://arxiv.org/abs/2401.xxxxx)

---

## License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.

```
MIT License

Copyright (c) 2026 Arjun Silwal

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

[Full text in LICENSE file]
```

---

## Maintainers

- **Lead**: [Arjun Silwal](https://github.com/Arjunsilwal)

## Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/Arjunsilwal/ASvLLM/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/Arjunsilwal/ASvLLM/discussions)

---

**Last Updated**: April 2026  
**Status**: Active Research  )
