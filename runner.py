# runner.py
import os
import argparse
import pygame

# scenarios imported here
from game_manager import GameManager
from scenario_generator import (
    head_on_scenario,
    cross_over_scenario,
    over_taking_scenario,
    multi_vessel_scenario,
    multi_vessel_scenario_2,
)

SCENARIOS = {
    "head_on": head_on_scenario,
    "crossing": cross_over_scenario,
    "overtaking": over_taking_scenario,
    "multi": multi_vessel_scenario,
    "multi2": multi_vessel_scenario_2,
}


def run_experiment(scenario_name, width, height, run_idx, outdir, prefix="detailed_prompt"):
    # 1) Headless mode & init
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.init()   # make sure display subsystem is up

    # 2) Build game, set up scenario
    gm = GameManager(width, height)
    em = gm.entity_manager
    SCENARIOS[scenario_name](em, width, height)
    em.movement_active = True

    # 3) Step until all vessels clear their goals
    clock = pygame.time.Clock()
    while any(v.goal for v in em.vessels):
        dt = clock.tick(60) / 1000.0
        gm.update(dt)

    # 4) Export that run’s log
    os.makedirs(outdir, exist_ok=True)
    fname = f"{prefix}_{scenario_name}_experiment_{run_idx}.csv"
    em.export_log(os.path.join(outdir, fname))
    print(f"→ wrote {fname}")

    # 5) Tear down before next run
    pygame.display.quit()
    pygame.quit()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", choices=SCENARIOS, required=True)
    p.add_argument("--runs",     type=int,   default=1)
    p.add_argument("--outdir",   type=str,   default="experiments")
    p.add_argument("--width",    type=int,   default=800)
    p.add_argument("--height",   type=int,   default=600)
    args = p.parse_args()

    for i in range(9, args.runs + 1):
        run_experiment(
            args.scenario,
            args.width,
            args.height,
            i,
            args.outdir,
            prefix="detailed_prompt"
        )


if __name__ == "__main__":
    main()
