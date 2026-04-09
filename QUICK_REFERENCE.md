# ASvLLM Quick Reference

A fast lookup guide for common tasks, file locations, and troubleshooting.

---

## 📁 File Structure Quick Map

| Component | Files | Purpose |
|-----------|-------|---------|
| **Simulator Core** | `entity.py`, `game_manager.py`, `graphics_manager.py`, `event_manager.py`, `ui_manager.py` | Pygame-based multi-vessel simulator |
| **Decision Logic** | `entity_manager_standard.py`, `entity_manager_prompt_history.py`, `entity_manager_natural_language.py` | 3 decision modes (text, history, vision) |
| **LLM Integration** | `llm_text_manager.py`, `llm_vision_manager.py`, `response_parser.py` | LLM API calls + response processing |
| **Prompts** | `prompts_generator/[5 files]` | 5 abstraction levels + TSS mode |
| **Batch Automation** | `batch_runner.py`, `clear_data.py` | Experiment loops, data cleanup |
| **Analysis** | `master_analysis.py`, `ablation_study.py`, `mode_prompt_study.py`, `final_plots.py`, `run_all_analysis.py`, `analysis_utils.py`, `analysis_config.py` | ETL, metrics, figures |
| **Scenarios** | `scenario_generator.py` | 6 maritime encounter definitions |
| **Utilities** | `env_utils.py`, `response_parser.py`, `validate_logs.py`, `STAGE1_QUICKSTART.py` | Helpers, validation, testing |
| **Documentation** | `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTORS.md`, `PAPER_PLAN.md`, `STATUS_REPORT.md` | Guides, community, planning |
| **Config** | `requirements.txt`, `environment.yml`, `.gitignore` | Dependencies, version control |

---

## 🚀 Common Tasks

### ▶️ Run Interactive Simulator
```bash
python main.py
# Launches Pygame window with manual vessel control
# Default: Head-On Scenario, manual agent (keybaord controls)
```

### 🔄 Run Single LLM Decision Test
```bash
python batch_runner.py openai standard minimal "Head-On Scenario"
# Runs 1 scenario with 1 LLM query
# Use for quick testing before batch runs
```

### 📊 Run Full Batch Experiment (220+ LLM calls)
```bash
python batch_runner.py all
# Runs 10 iterations × all 22 configurations (3 modes × 3 providers × 5 prompts)
# 6 scenarios per config = ~2,640 LLM queries total
# Expected runtime: 2-3 weeks, cost: $500-800
```

### 📈 Generate Analysis (After data collection)
```bash
python run_all_analysis.py
# Executes full pipeline:
#   1. master_analysis.py → Consolidate logs, calculate metrics
#   2. ablation_study.py → Supplementary figures
#   3. mode_prompt_study.py → Interaction heatmaps
#   4. final_plots.py → Publication figures
# Outputs: figures/, study_results/, master_results.csv
```

### ✅ Validate Data Integrity
```bash
python validate_logs.py
# Checks all CSV files in logs/ for:
#   - Missing columns
#   - Type errors
#   - Missing LLM decisions
#   - Malformed JSON responses
```

### 🧹 Clean All Results & Logs
```bash
python clear_data.py
# Removes: logs/*.csv, figures/*, study_results/*.csv, master_results.csv
# WARNING: Irreversible! Backup before running
```

### 📋 Run Stage 1 Validation
```bash
python STAGE1_QUICKSTART.py
# 7-step validation workflow:
#   1. Check dependencies
#   2. Verify LLM credentials
#   3. Test LLM connection
#   4. Run minimal test case
#   5. Validate data collection
#   6. Generate basic plots
#   7. Report stage completion
```

---

## 🎮 Interactive Simulator Controls

When running `python main.py`:

| Control | Action |
|---------|--------|
| **Arrow Keys** | Change heading of your (blue) vessel |
| **W/S** | Increase/decrease speed |
| **SPACE** | Execute a maneuver (if collision predicted) |
| **P** | Pause simulation |
| **U** | Unpause simulation |
| **R** | Reset scenario |
| **L** | Toggle LLM decision logging |
| **ESC** | Quit |

---

## 📊 Output Files Location

| Output | Location | Format | Created By |
|--------|----------|--------|-----------|
| LLM Interaction Logs | `logs/results_*_{mode}_{provider}.csv` | CSV | `batch_runner.py` |
| Master Results | `master_results.csv` (root) | CSV | `master_analysis.py` |
| Run Summary | `logs/run_summary.csv` | CSV | `batch_runner.py` |
| Ablation Figures | `figures/ablation_*.png` | PNG | `ablation_study.py` |
| Publication Figures | `figures/fig[1-4].png` | PNG | `final_plots.py` |
| Heatmaps | `study_results/heatmap_*.png` | PNG | `mode_prompt_study.py` |
| Supplementary Plots | `study_results/*.png` | PNG | `master_analysis.py` |

---

## 🔧 Configuration Quick Edit

### Change LLM Provider
**File**: `batch_runner.py` (line ~50)
```python
PROVIDERS = ["openai", "claude", "deepseek"]  # Edit this list
```

### Adjust Prompt Details
**File**: `prompts_generator/detailed_prompt.py`
- Edit system prompt (line ~15)
- Edit user instruction (line ~35)
- Edit COLREGs context (lines ~40-60)

### Change Scenario Parameters
**File**: `scenario_generator.py`
- Line ~30: Initial vessel positions
- Line ~50: Goal positions
- Line ~70: Encounter type descriptions

### Modify LLM Decision Thresholds
**File**: `entity_manager_standard.py` (line ~80)
```python
COLLISION_RISK_THRESHOLD = 0.5  # Default: trigger maneuver if risk > 50%
```

---

## 🐛 Troubleshooting Quick Fixes

### "No available video device" Error
**Cause**: Running on headless system (WSL, SSH, Docker)
**Fix**:
```bash
export DISPLAY=:0  # Linux/WSL: try virtual display
# OR run analysis-only (no graphics)
python -c "from master_analysis import *; analyze_all()"
```

### "Invalid API Key" Error
**Cause**: Missing or expired LLM credentials
**Fix**:
```bash
# Create .env file in project root
echo "OPENAI_API_KEY=your_key_here" > .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```
Restart Python to pick up new credentials.

### "JSON Decode Error" in LLM Response
**Cause**: LLM response not valid JSON
**Fix**: Already handled by `response_parser.py` (uses regex fallback)
- Check logs for `[WARNING] Invalid JSON` messages
- May indicate LLM confused by prompt; try different prompt level

### Missing Columns in Analysis Output
**Cause**: Logs generated with old format
**Fix**:
```bash
python clear_data.py  # Remove old logs
python batch_runner.py openai standard minimal "Head-On Scenario"  # Collect new
python run_all_analysis.py  # Re-analyze
```

### Pygame Window Crashes on Start
**Cause**: Graphics driver issues
**Fix**:
```bash
# Use headless mode (no visualization)
python -c "
from batch_runner import run_experiment
# Will skip graphics rendering
"
```

### Out of Memory During Analysis
**Cause**: Too many figures loaded simultaneously
**Fix**: Run analysis scripts individually
```bash
python master_analysis.py  # Stage 1
python ablation_study.py   # Stage 2
python mode_prompt_study.py  # Stage 3
python final_plots.py      # Stage 4
```

---

## 📚 Key Classes & Functions

### Entity Class
```python
from entity import Vessel, Maneuver

# Create vessel
v = Vessel(x=100, y=200, heading=1.57, speed=5.0)

# Control vessel
v.set_maneuver(Maneuver.ALTER_COURSE_PORT)
v.execute_maneuver()

# Check collision risk
distance_to_target_km = v.distance_to(target_vessel)
dcpa_km = v.calculate_dcpa(target_vessel)
```

### LLM Text Manager
```python
from llm_text_manager import LLMTextManager

llm = LLMTextManager(provider="openai", model="gpt-5.2")
response = await llm.query_llm(prompt_text)  # Async call
maneuver = parse_llm_response_for_all(response)  # Get Maneuver enum
```

### Analysis Functions
```python
from analysis_utils import *

# Extract rule number from LLM response
rule_num = extract_rule_num(response_text)

# Calculate COLREGs alignment
alignment_score = calculate_alignment(actual_maneuver, rule_num)

# Add analysis columns to dataframe
df = add_analysis_columns(df)

# Calculate all metrics
metrics = calculate_metrics(df)
```

---

## 📖 Documentation Map

| Document | Purpose | Target Audience |
|----------|---------|-----------------|
| `README.md` | Comprehensive overview + usage guide | Everyone |
| `PAPER_PLAN.md` | 7-stage publication roadmap | Project team |
| `CONTRIBUTING.md` | How to contribute code | Developers |
| `CHANGELOG.md` | Version history + planned releases | Users, Devs |
| `CODE_OF_CONDUCT.md` | Community standards | Community members |
| `CONTRIBUTORS.md` | Credit to contributors | Everyone |
| `STATUS_REPORT.md` | Code review findings (if exists) | Project team |
| `IMPLEMENTATION_SUMMARY.md` | Tech strategy overview (if exists) | Project team |

---

## 🔑 Important Constants

**Decision Modes**:
- `standard` - Text-only decisions
- `prompt_history` - Text with 3-5 timestep memory
- `natural` - Natural language with vision

**LLM Providers**:
- `openai` - OpenAI GPT-5.2
- `claude` - Anthropic Claude Sonnet 4.5
- `deepseek` - DeepSeek Chat

**Prompts**:
- `minimal` - Bare essentials
- `moderate` - Standard info
- `detailed` - Full context + rules
- `natural` - Conversational tone
- `tss` - Traffic Separation Scheme

**Scenarios** (6 types):
- `Head-On Scenario`
- `Crossing Scenario`
- `Overtaking Scenario`
- `Multi-Vessel Scenario 1/2/3`

**Maneuvers** (Response Parser Output):
- `MAINTAIN_COURSE_SPEED`
- `ALTER_COURSE_STARBOARD` / `ALTER_COURSE_PORT`
- `REDUCE_SPEED`
- `ACCELERATE`
- `PASS_ASTERN`

---

## 💡 Performance Tips

### Speed Up Analysis
```bash
# Skip recreating existing plots
python - <<EOF
from analysis_config import *
from analysis_utils import *
import pandas as pd

df = pd.read_csv(MASTER_RESULTS_PATH)
print_metrics(df)  # Quick stats without plotting
EOF
```

### Reduce LLM Cost
- Use `minimal` prompt (costs same in tokens, captures essentials)
- Use `deepseek` provider (cheap alternative to OpenAI/Claude)
- Start with 2-3 configurations for testing before full batch

### Parallel Batch Runs
```bash
# Run different providers in parallel terminals
terminal1: python batch_runner.py openai
terminal2: python batch_runner.py claude
terminal3: python batch_runner.py deepseek
```

---

## 📞 Support Resources

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **README.md**: Comprehensive troubleshooting guide
- **CONTRIBUTING.md**: Development guidelines

---

## ✅ Validation Checklist

Before submitting code changes:

- [ ] Code follows PEP 8 (run `black *.py`)
- [ ] All functions have docstrings
- [ ] New functions include type hints
- [ ] No hardcoded file paths (use `analysis_config.py` constants)
- [ ] No duplicate imports or functions
- [ ] Tested with single scenario before batch run
- [ ] Updated `CHANGELOG.md` with changes
- [ ] Created GitHub issue (or linked existing one)

---

Last updated: April 9, 2026
For latest updates, see [CHANGELOG.md](CHANGELOG.md)
