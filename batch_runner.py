import os
import sys
import csv
import math
import asyncio
import pygame
from game_manager import GameManager
from env_utils import load_project_env

# --- RESEARCH CONFIGURATION ---
ALL_PROVIDERS = ["openai", "claude", "deepseek"]

# Independent Variable 1: Intelligence Level
ALL_MODES = ["standard", "prompt_history", "natural"]

# Independent Variable 3: Scenario Complexity
STANDARD_SCENARIOS = [
    "Head-On Scenario",
    "Cross Over Scenario",
    "Over Taking Scenario",
    "Multi vessel Scenario",
    "Multi vessel Scenario 2",
    "Multi vessel Scenario 3"
]

RUNS_PER_CONFIG = 10
SECONDS_PER_RUN = 55
COLLISION_DISTANCE_PX = 20.0
RUN_SUMMARY_PATH = "logs/run_summary.csv"
RUN_SUMMARY_FIELDS = [
    "Experiment ID",
    "LLM Provider",
    "Mode",
    "Requested Prompt",
    "Effective Prompt",
    "Scenario",
    "Run Number",
    "Elapsed Time (s)",
    "All Reached Goal",
    "Reached Goal Fraction",
    "Any Collision",
    "Collision Count",
    "Min Pairwise Distance (px)",
    "Min Pairwise Distance (km)",
    "LLM Calls",
]


def ensure_run_summary_log():
    os.makedirs("logs", exist_ok=True)
    if not os.path.exists(RUN_SUMMARY_PATH):
        with open(RUN_SUMMARY_PATH, "w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=RUN_SUMMARY_FIELDS).writeheader()


def resolve_effective_prompt(mode, prompt, scenario):
    if scenario == "Traffic Separation Scenario" or prompt == "tss":
        return "tss"
    if mode == "prompt_history":
        return "natural_history"
    if mode == "natural":
        return "natural_vision"
    return prompt


def compute_pairwise_metrics(vessels):
    min_distance_px = None
    collision_count = 0

    for i, vessel_a in enumerate(vessels):
        for vessel_b in vessels[i + 1:]:
            distance_px = math.hypot(vessel_a.x - vessel_b.x, vessel_a.y - vessel_b.y)
            if min_distance_px is None or distance_px < min_distance_px:
                min_distance_px = distance_px
            if distance_px < COLLISION_DISTANCE_PX:
                collision_count += 1

    return min_distance_px, collision_count


def append_run_summary(row):
    with open(RUN_SUMMARY_PATH, "a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=RUN_SUMMARY_FIELDS).writerow(row)


def get_mode_prompt_matrix(target_llm):
    """
    Returns mode -> prompt list.
    We intentionally mirror actual manager behavior to avoid duplicate/imbalanced logs.
    - standard: supports all text prompt levels
    - prompt_history: effectively uses natural-history style
    - natural: vision/natural mode (disabled for DeepSeek)
    """
    matrix = {
        "standard": ["minimal", "moderate", "detailed", "natural"],
        "prompt_history": ["natural"],
        "natural": ["natural"]
    }

    if target_llm == "deepseek":
        matrix.pop("natural", None)

    return matrix


async def run_simulation_step(game, mode, llm, prompt, scenario, run_num, experiment_id):
    """Executes a single simulation instance."""
    print(
        f"\n--- [EXP {experiment_id}] {llm.upper()} | {mode} | {prompt} | {scenario} | Run {run_num}/{RUNS_PER_CONFIG} ---")

    effective_prompt = resolve_effective_prompt(mode, prompt, scenario)
    min_pairwise_distance_px = None
    collision_count = 0
    elapsed = 0.0

    try:
        game.load_simulation_scripted(
            mode=mode,
            llm=llm,
            prompt=prompt,
            scenario=scenario,
            experiment_id=experiment_id
        )

        start_time = pygame.time.get_ticks()
        clock = pygame.time.Clock()
        run_active = True

        while run_active:
            # 30 FPS cap for consistent physics across parallel runs
            dt = min(clock.tick(60) / 1000.0, 1 / 30)
            pygame.event.pump()

            if game.entity_manager:
                await game.entity_manager.update_vessels(dt)
                run_min_distance_px, run_collision_count = compute_pairwise_metrics(game.entity_manager.vessels)
                if run_min_distance_px is not None:
                    if min_pairwise_distance_px is None or run_min_distance_px < min_pairwise_distance_px:
                        min_pairwise_distance_px = run_min_distance_px
                collision_count += run_collision_count

            game.render()

            elapsed = (pygame.time.get_ticks() - start_time) / 1000.0

            if elapsed > SECONDS_PER_RUN:
                run_active = False

            if game.entity_manager and all(v.reached_goal for v in game.entity_manager.vessels):
                print(f"  > Success: All vessels arrived.")
                run_active = False

            await asyncio.sleep(0)

    except Exception as e:
        print(f"CRITICAL ERROR in Exp {experiment_id}: {e}")
    finally:
        vessels = game.entity_manager.vessels if game.entity_manager else []
        reached_goal_count = sum(1 for vessel in vessels if vessel.reached_goal)
        vessel_count = len(vessels)
        all_reached_goal = bool(vessels) and reached_goal_count == vessel_count
        reached_goal_fraction = (reached_goal_count / vessel_count) if vessel_count else 0.0
        min_pairwise_distance_px = min_pairwise_distance_px if min_pairwise_distance_px is not None else -1.0
        min_pairwise_distance_km = (
            min_pairwise_distance_px / game.entity_manager.pixels_per_km
            if game.entity_manager and min_pairwise_distance_px >= 0
            else -1.0
        )
        llm_calls = game.entity_manager.llm_call_count if game.entity_manager else 0

        append_run_summary({
            "Experiment ID": experiment_id,
            "LLM Provider": llm,
            "Mode": mode,
            "Requested Prompt": prompt,
            "Effective Prompt": effective_prompt,
            "Scenario": scenario,
            "Run Number": run_num,
            "Elapsed Time (s)": f"{elapsed:.2f}",
            "All Reached Goal": all_reached_goal,
            "Reached Goal Fraction": f"{reached_goal_fraction:.4f}",
            "Any Collision": collision_count > 0,
            "Collision Count": collision_count,
            "Min Pairwise Distance (px)": f"{min_pairwise_distance_px:.2f}",
            "Min Pairwise Distance (km)": f"{min_pairwise_distance_km:.4f}",
            "LLM Calls": llm_calls,
        })


async def run_batch(target_llm):
    """Orchestrates the batch runs with provider-specific filtering."""
    pygame.init()
    game = GameManager(1200, 800)

    # OFFSET IDs for distinct datasets
    id_offsets = {"openai": 0, "claude": 2000, "deepseek": 4000}
    global_exp_id = 1 + id_offsets.get(target_llm, 0)

    print(f"=== PARALLEL DATA COLLECTION: {target_llm.upper()} ===")

    # Check for API key
    key_env = f"{target_llm.upper() if target_llm != 'claude' else 'CLAUDE'}_API_KEY"
    if not os.getenv(key_env):
        print(f"!!! ERROR: {key_env} not found. Exiting. !!!")
        pygame.quit()
        return

    mode_prompt_matrix = get_mode_prompt_matrix(target_llm)
    if target_llm == "deepseek":
        print(f"  > Note: 'natural' mode disabled for {target_llm} (No vision support)")

    print("  > Planned experiment matrix:")
    for mode, prompts in mode_prompt_matrix.items():
        print(f"    - {mode}: {prompts}")

    for mode, prompts in mode_prompt_matrix.items():
        for prompt in prompts:
            for scenario in STANDARD_SCENARIOS:
                for r in range(1, RUNS_PER_CONFIG + 1):
                    await run_simulation_step(game, mode, target_llm, prompt, scenario, r, global_exp_id)
                    global_exp_id += 1

    print(f"\n=== BATCH COMPLETE FOR {target_llm.upper()} ===")
    pygame.quit()


async def run_batch_sequence(providers):
    for provider in providers:
        await run_batch(provider)


if __name__ == "__main__":
    load_project_env()
    ensure_run_summary_log()

    if len(sys.argv) > 1:
        selected = sys.argv[1].lower()
        if selected == "all":
            asyncio.run(run_batch_sequence(ALL_PROVIDERS))
        elif selected in ALL_PROVIDERS:
            asyncio.run(run_batch(selected))
        else:
            print(f"Invalid provider. Choose from: {ALL_PROVIDERS + ['all']}")
    else:
        print("Please specify a provider: python3 batch_runner.py [openai|claude|deepseek|all]")
