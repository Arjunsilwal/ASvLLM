# runner.py
import os
import sys
import argparse
import pygame

# <-- IMPORTANT: this makes pygame run “headless,” no window pops up.
os.environ["SDL_VIDEODRIVER"] = "dummy"

from game_manager import GameManager

from scenario_generator import (
    head_on_scenario,
    cross_over_scenario,
    over_taking_scenario,
    multi_vessel_scenario,
)

SCENARIOS = {
    "head_on": head_on_scenario,
    "crossing": cross_over_scenario,
    "overtaking": over_taking_scenario,
    "multi": multi_vessel_scenario,
}


def run_experiment(scenario_name, width, height, run_idx, outdir, prefix="detailed_prompt"):
    pygame.init()
    gm = GameManager(width, height)
    em = gm.entity_manager
    SCENARIOS[scenario_name](em, width, height)
    em.movement_active = True

    clock = pygame.time.Clock()

    while any(v.goal for v in em.vessels):
        dt = clock.tick(60) / 1000.0
        gm.update(dt)

    # build the filename exactly how you want:
    fname = f"{prefix}_{scenario_name}_experiment_{run_idx}.csv"
    os.makedirs(outdir, exist_ok=True)
    em.export_log(os.path.join(outdir, fname))
    print(f"→ wrote {fname}")
    pygame.quit()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", choices=SCENARIOS, required=True)
    p.add_argument("--runs", type=int, default=1)
    p.add_argument("--outdir", type=str, default="experiments")
    p.add_argument("--width", type=int, default=800)
    p.add_argument("--height", type=int, default=600)
    args = p.parse_args()

    for i in range(1, args.runs + 1):
        run_experiment(
            args.scenario,
            args.width,
            args.height,
            i,
            args.outdir
        )


if __name__ == "__main__":
    main()