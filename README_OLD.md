# ASvLLM: LLM-Driven Autonomous Vessel Navigation

ASvLLM is a COLREGs-aware autonomous surface vessel (ASV) simulator built with Pygame, where an LLM acts as the **main decision maker** for collision-avoidance maneuvers.  
The simulator supports multiple decision modes, prompt levels, and model providers so you can compare behavior, reliability, and rule alignment across configurations.

## What This Project Does

- Simulates multi-vessel encounter scenarios (head-on, crossing, overtaking, multi-vessel, and traffic separation).
- Detects likely collision risk using relative-motion prediction (TCPA/DCPA-style checks).
- Sends relevant vessel context to an LLM and receives structured maneuver decisions.
- Applies the selected maneuver to vessel dynamics in real time.
- Logs outcomes for quantitative evaluation and research analysis.

## LLM as the Core Decision Layer

In this project, the LLM is not just a helper. It is the **primary tactical planner**:

1. The entity manager detects conflict candidates.
2. A prompt builder converts vessel state/history/scenario into structured instructions.
3. The LLM returns JSON decisions (action + explanation/rule reference).
4. The parser maps LLM text into executable maneuvers.
5. Vessel control logic executes the maneuver in the simulator loop.

This pipeline is implemented mainly through:

- `entity_manager_standard.py`
- `entity_manager_prompt_history.py`
- `entity_manager_natural_language.py`
- `llm_text_manager.py`
- `llm_vision_manager.py`
- `response_parser.py`

## Prompt Levels and Decision Modes

The system varies two key dimensions independently: **decision mode** and **prompt type**.

### Decision Modes (`mode`)

- `standard`: text-only decision loop with selectable prompt style.
- `prompt_history`: text decision loop that includes short temporal memory (previous vessel states and responses).
- `natural`: vision-assisted decision loop (image + natural-language context; DeepSeek falls back to text).

### Prompt Types (`prompt`)

- `minimal`: compact, low-token state description.
- `moderate`: medium-detail prompt with more procedural context.
- `detailed`: high-detail prompt emphasizing richer collision context.
- `natural`: narrative, human-like maritime context prompt.
- `tss`: specialized prompt for Rule 10 / Traffic Separation Scheme behavior.

## Supported LLM Providers

- `openai` (model: `gpt-5.2-2025-12-11`)
- `claude` (model: `claude-sonnet-4-5-20250929`)
- `deepseek` (model: `deepseek-chat`)

Required environment variables:

- `OPENAI_API_KEY`
- `CLAUDE_API_KEY`
- `DEEPSEEK_API_KEY`

## Project Structure (Core Files)

- `main.py`: async app entry point.
- `game_manager.py`: top-level orchestrator (UI state, mode/provider/prompt selection, manager loading).
- `ui_manager.py`: dropdowns/buttons for mode, provider, scenario, prompt.
- `scenario_generator.py`: encounter definitions.
- `entity.py`: vessel dynamics and maneuver execution.
- `batch_runner.py`: automated repeated experiments over mode/prompt/scenario/provider combinations.
- `master_analysis.py`: aggregate metrics and consolidated result table generation.
- `ablation_study.py`, `mode_prompt_study.py`, `final_plots.py`: analysis and figure generation scripts.

## Quick Start

## 1) Create and activate a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 2) Install dependencies

Install the libraries used in this codebase (Pygame + LangChain provider SDKs):

```bash
pip install pygame langchain-openai langchain-anthropic langchain-core
```

## 3) Set API keys

Create a `.env` file in the project root or export the keys in your shell.

```bash
OPENAI_API_KEY="your_openai_key"
CLAUDE_API_KEY="your_claude_key"
DEEPSEEK_API_KEY="your_deepseek_key"
```

## 4) Run interactive simulation

```bash
python3 main.py
```

Use the top navigation bar to select:

- Mode (`standard`, `prompt_history`, `natural`)
- LLM provider (`openai`, `claude`, `deepseek`)
- Scenario
- Prompt type (`minimal`, `moderate`, `detailed`, `natural`, `tss`)

Then click **LOAD**.

## Batch Experiments

Run repeated evaluations by provider:

```bash
python3 batch_runner.py openai
python3 batch_runner.py claude
python3 batch_runner.py deepseek
python3 batch_runner.py all
```

Optional cleanup before new runs:

```bash
python3 clear_data.py
```

## Outputs and Logs

Simulation logs are written under `logs/`, including:

- `logs/results_standard_<provider>.csv`
- `logs/results_history_<provider>.csv`
- `logs/results_natural_<provider>.csv`
- `logs/run_summary.csv` (scenario-level run outcomes: goal completion, collision flag, min separation, elapsed time, LLM calls)

Post-processing outputs include:

- `master_results.csv`
- `master_run_results.csv`
- plots in root and `figures/`

## Analysis Pipeline

After collecting runs:

```bash
python3 master_analysis.py
python3 ablation_study.py
python3 mode_prompt_study.py
python3 final_plots.py
```

## Notes

- `deepseek` does not provide equivalent vision-path behavior in this project and uses text fallback in natural mode.
- `entity_manager_rag.py` exists as an alternate/legacy path but is not the primary mode mapping used by the UI loader.
