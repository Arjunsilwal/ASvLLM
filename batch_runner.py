import asyncio
import pygame
from game_manager import GameManager
import os

# --- EXPERIMENT CONFIGURATION ---

# 1. Which LLMs to test?
LLM_PROVIDERS = ["openai"]
# Uncomment to test others (requires API keys in env):
# LLM_PROVIDERS = ["openai", "claude", "deepseek"]

# 2. Which Levels to test?
# Format: (Mode, PromptType)
LEVELS = [
    ("standard", "minimal"),  # Level 1: Baseline
    ("prompt_history", "natural"),  # Level 2: Temporal Context
    ("natural", "natural")  # Level 3: Full System (Vision)
]

# 3. Which Scenarios to test?
SCENARIOS = [
    "Head-On Scenario",
    "Cross Over Scenario",
    "Over Taking Scenario",
    "Multi vessel Scenario",
    "Traffic Separation Scenario"
]

RUNS_PER_SCENARIO = 5  # For journal, set to 10
SECONDS_PER_RUN = 50  # Duration of each run


async def run_batch():
    # Initialize pygame (needed for headless rendering too)
    pygame.init()

    # Create window once
    game = GameManager(1000, 800)

    print(f"=== STARTING AUTOMATED BATCH DATA COLLECTION ===")
    print(f"LLMs: {LLM_PROVIDERS}")
    print(f"Levels: {len(LEVELS)}")
    print(f"Scenarios: {len(SCENARIOS)}")
    print(f"Total Runs: {len(LLM_PROVIDERS) * len(LEVELS) * len(SCENARIOS) * RUNS_PER_SCENARIO}")

    for llm in LLM_PROVIDERS:
        # Check if key exists for this provider before starting
        env_key = f"{'OPENAI' if llm == 'openai' else 'CLAUDE' if llm == 'claude' else 'DEEPSEEK'}_API_KEY"
        if not os.getenv(env_key):
            print(f"SKIP: {llm} (API Key {env_key} not found)")
            continue

        for mode, prompt in LEVELS:
            for scenario in SCENARIOS:
                for run_num in range(1, RUNS_PER_SCENARIO + 1):
                    print(f"\n--- RUNNING: {llm} | {mode} | {scenario} | Attempt {run_num} ---")

                    try:
                        # 1. Load the specific configuration
                        game.load_simulation_scripted(
                            mode=mode,
                            llm=llm,  # <-- Pass the LLM provider here
                            prompt=prompt,
                            scenario=scenario
                        )

                        # 2. Run the simulation loop
                        start_time = pygame.time.get_ticks()
                        clock = pygame.time.Clock()

                        run_active = True
                        while run_active:
                            # Tick clock but cap dt for physics stability
                            raw_dt = clock.tick(60) / 1000.0
                            dt = min(raw_dt, 1 / 30)

                            # Process events to keep OS happy
                            pygame.event.pump()

                            # Update AI and Physics
                            await game.entity_manager.update_vessels(dt)

                            # Render (Required for Vision/Screenshots)
                            game.render()

                            # Check time limit
                            elapsed = (pygame.time.get_ticks() - start_time) / 1000.0
                            if elapsed > SECONDS_PER_RUN:
                                run_active = False

                            await asyncio.sleep(0)  # Yield to event loop

                    except Exception as e:
                        print(f"CRITICAL ERROR in run {run_num}: {e}")
                        continue  # Keep going to next run

    print("\n=== ALL EXPERIMENTS COMPLETE ===")
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(run_batch())