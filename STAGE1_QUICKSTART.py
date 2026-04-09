#!/usr/bin/env python3
"""
STAGE 1 QUICK START GUIDE
For ASvLLM Ocean Engineering Paper Publication

This file provides copy-paste commands to validate your codebase readiness.
Run these commands in sequence. Each should complete successfully before moving to the next.

Timeline: ~2-3 hours
"""

print("""
╔══════════════════════════════════════════════════════════════════════╗
║                     STAGE 1: VALIDATION & SETUP                       ║
║              Ocean Engineering Paper - ASvLLM Project                 ║
╚══════════════════════════════════════════════════════════════════════╝

📋 PRE-REQUISITES:
  ✓ Python 3.8+ installed
  ✓ Virtual environment activated
  ✓ Dependencies installed: pip install pygame langchain-openai langchain-anthropic
  ✓ API keys set: OPENAI_API_KEY, CLAUDE_API_KEY, DEEPSEEK_API_KEY
  ✓ Working directory: /home/arjun/Desktop/ASvLLM

ESTIMATED TIME: 2-3 hours
DIFFICULTY: 🟢 Easy

═════════════════════════════════════════════════════════════════════════

STEP 1: ENVIRONMENT CHECK ⏱️ (5 minutes)
───────────────────────────────────────────────────────────────────────

This verifies your Python setup and API keys are loaded correctly.

RUN THIS:
$ python3 -c "
from env_utils import load_project_env
import os
load_project_env()

print('\\n✅ Environment Check Results:')
print(f'   OPENAI_API_KEY: {\"✓ SET\" if os.getenv(\"OPENAI_API_KEY\") else \"❌ MISSING\"}')
print(f'   CLAUDE_API_KEY: {\"✓ SET\" if os.getenv(\"CLAUDE_API_KEY\") else \"❌ MISSING\"}')
print(f'   DEEPSEEK_API_KEY: {\"✓ SET\" if os.getenv(\"DEEPSEEK_API_KEY\") else \"❌ MISSING\"}')

try:
    import pygame
    print(f'   Pygame: ✓ {pygame.__version__}')
except:
    print('   ❌ Pygame not installed')

try:
    from langchain_openai import ChatOpenAI
    from langchain_anthropic import ChatAnthropic
    print('   LangChain: ✓ Available')
except:
    print('   ❌ LangChain not installed')

print('\\n✅ ALL READY - Proceed to STEP 2')
"

EXPECTED OUTPUT:
  ✓ SET for all three API keys
  ✓ Pygame version shown
  ✓ LangChain available
  ✓ Message: "ALL READY - Proceed to STEP 2"

TROUBLESHOOTING:
  - Missing API key? Create .env file with: OPENAI_API_KEY=your_key
  - Pygame error? Run: pip install pygame
  - LangChain error? Run: pip install langchain-openai langchain-anthropic

═════════════════════════════════════════════════════════════════════════

STEP 2: DATA CLEANUP ⏱️ (2 minutes)
───────────────────────────────────────────────────────────────────────

Wipes old logs to ensure a clean dataset.

RUN THIS:
$ python3 clear_data.py

EXPECTED OUTPUT:
  ✓ Confirming deletion...
  ✓ Removed old log files
  ✓ logs/ directory ready
  ✓ Cleanup complete

═════════════════════════════════════════════════════════════════════════

STEP 3: VALIDATION SCRIPT TEST ⏱️ (1 minute)
───────────────────────────────────────────────────────────────────────

Runs the data validator on empty logs (sanity check).

RUN THIS:
$ python3 validate_logs.py

EXPECTED OUTPUT:
  ⚠️ "Error: No result files found in 'logs/'" or equivalent
  (This is expected when logs are empty; shows validate_logs.py works)

═════════════════════════════════════════════════════════════════════════

STEP 4: SINGLE SIMULATION RUN (QUICK TEST) ⏱️ (5-10 minutes)
───────────────────────────────────────────────────────────────────────

Runs ONE simulation to verify the entire pipeline works.
This tests: game manager, entity manager, LLM calls, logging, no crashes.

RUN THIS:
$ python3 -c "
import asyncio
import pygame
from game_manager import GameManager

async def quick_test():
    pygame.init()
    game = GameManager(1000, 1000)
    game.load_simulation_scripted(
        mode='standard',
        llm='openai',
        prompt='minimal',
        scenario='Head-On Scenario',
        experiment_id=1
    )
    
    clock = pygame.time.Clock()
    elapsed = 0
    max_time = 15  # Run for 15 seconds
    
    print('Running 15-second simulation... (This is a quick smoke test)')
    while elapsed < max_time:
        dt = clock.tick(60) / 1000.0
        await game.entity_manager.update_vessels(dt)
        elapsed += dt
        if elapsed % 5 < 0.1:  # Print every ~5 seconds
            print(f'  ✓ {int(elapsed)}s elapsed...')
    
    print(f'✓ Simulation completed in {elapsed:.1f}s')
    print(f'✓ LLM calls made: {game.entity_manager.llm_call_count}')
    print(f'✓ Check logs/results_standard_openai.csv for entries')
    pygame.quit()

asyncio.run(quick_test())
"

EXPECTED OUTPUT:
  ✓ Simulation runs for 15 seconds
  ✓ LLM call count > 0
  ✓ No crashes
  ✓ New rows in logs/results_standard_openai.csv

IF IT BREAKS:
  Common issues:
  - JSONDecodeError → Prompt has non-ASCII characters (llm_text_manager.py has fix)
  - API error → Check OPENAI_API_KEY is valid
  - Pygame error → Usually from display; if headless, that's fine

═════════════════════════════════════════════════════════════════════════

STEP 5: VALIDATE LOGS ⏱️ (1 minute)
───────────────────────────────────────────────────────────────────────

Checks the newly created log file for data quality.

RUN THIS:
$ python3 validate_logs.py

EXPECTED OUTPUT:
  ✓ "Loaded logs/results_standard_openai.csv: X rows"
  ✓ "All accuracy values in valid range [0.0, 1.0]"
  ✓ "All LLM responses contain valid JSON"
  ✓ "SUMMARY: All checks PASSED"

═════════════════════════════════════════════════════════════════════════

STEP 6: MASTER ANALYSIS (OPTIONAL) ⏱️ (2 minutes)
───────────────────────────────────────────────────────────────────────

Runs the analysis pipeline on current (small) dataset.
This validates that master_analysis.py works correctly.

RUN THIS:
$ python3 master_analysis.py

EXPECTED OUTPUT:
  ✓ "Merging 1 files..."
  ✓ "OFFICIAL RESEARCH METRICS"
  ✓ CSV files created: master_results.csv, master_run_results.csv
  ✓ One or more plots generated

═════════════════════════════════════════════════════════════════════════

STEP 7: FINAL PLOTS (OPTIONAL) ⏱️ (1 minute)
───────────────────────────────────────────────────────────────────────

Generates final publication-ready figures.

RUN THIS:
$ python3 final_plots.py

EXPECTED OUTPUT:
  ✓ 4 PNG files in figures/ directory
  ✓ Files named: fig1_accuracy_ablation.png, fig2_reliability_ablation.png, etc.
  ✓ No errors

═════════════════════════════════════════════════════════════════════════

✅ STAGE 1 COMPLETE!
───────────────────────────────────────────────────────────────────────

If all 7 steps passed, you are ready to proceed to STAGE 2.

NEXT ACTIONS:
  1. Review updated PAPER_PLAN.md (entire document, ~15 minutes)
  2. Create baseline_colregs_deterministic.py (see STAGE 1.4 in PAPER_PLAN.md)
  3. Once baseline is working, run STAGE 2 (full data collection): 2-3 weeks

═════════════════════════════════════════════════════════════════════════

🐛 TROUBLESHOOTING GUIDE
───────────────────────────────────────────────────────────────────────

PROBLEM: "OPENAI_API_KEY not found"
SOLUTION: 
  - Check if .env file exists in project root
  - If not, create it: echo "OPENAI_API_KEY=sk-..." > .env
  - Or set in shell: export OPENAI_API_KEY=sk-...

PROBLEM: "Error: Failed to decode JSON response"
SOLUTION:
  - This is a encoding error in prompt (smart quotes, accents)
  - llm_text_manager._setup_llm() has fallback ASCII encoding
  - If still fails, check for non-ASCII in prompt generators

PROBLEM: "pygame.error: No available video device"
SOLUTION:
  - If running on headless server, this is fine
  - Batch runs don't need display output
  - If you need to see graphics, run main.py locally with display

PROBLEM: "Rate limit error from OpenAI API"
SOLUTION:
  - Add delay between calls in batch_runner.py
  - Reduce RUNS_PER_CONFIG from 10 to 5 initially
  - Retry with exponential backoff

═════════════════════════════════════════════════════════════════════════

CHECKLIST: Mark off as you complete each step

□ STEP 1: Environment check (✓ all keys set)
□ STEP 2: Data cleanup (✓ logs wiped)
□ STEP 3: Validator works (✓ no files error is OK)
□ STEP 4: Single sim run (✓ completes in 15s)
□ STEP 5: Logs validated (✓ all checks passed)
□ STEP 6: Master analysis runs (✓ CSVs created)
□ STEP 7: Plots generated (✓ figures/ populated)

═════════════════════════════════════════════════════════════════════════

Questions? See STATUS_REPORT.md or PAPER_PLAN.md for details.

Good luck! 🚀
""")
