import time
import math
import json
import csv

# --- Imports ---
from entity import Vessel, ContextMenu
from scenario_generator import head_on_scenario, cross_over_scenario, over_taking_scenario, multi_vessel_scenario, \
    multi_vessel_scenario_2
from useLLm import get_llm_decision
from prompts_generator.low_prompt import generate_vessel_prompt
from response_parser import Maneuver, parse_llm_response_for_all


class EntityManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.vessels = []
        self.context_menu = None
        self.movement_active = False
        self.goal_queue = []

        # LLM cooldown dict: keys = id(vessel), values = last query time
        self.llm_cooldown = {}
        self.llm_cooldown_duration = 5.0  # seconds
        self.llm_trigger_distance_km = 0.30
        self.pixels_per_km = 1000.0

        # simulation clock
        self._sim_time = 0.0
        self.llm_call_count = 0

        self._log = []
        self._last_logged_time = -1.0
        self._last_prompt = None
        self._last_response = None

    def draw(self, screen):
        for vessel in self.vessels:
            vessel.draw(screen)
        if self.context_menu:
            self.context_menu.draw(screen)

    def show_context_menu(self, pos, options):
        self.context_menu = ContextMenu(pos[0], pos[1], options)

    def add_vessel(self, vessel):
        self.vessels.append(vessel)

    def handle_context_selection(self, selected_option):
        sw = self.game_manager.graphics_manager.width
        sh = self.game_manager.graphics_manager.height
        cx = self.context_menu.x + self.context_menu.width // 2
        cy = self.context_menu.y + self.context_menu.height // 2

        if selected_option == "Create Vessel":
            self.add_vessel(Vessel(cx, cy, self.pixels_per_km))
        elif selected_option == "Delete Vessel":
            for v in list(self.vessels):
                if v.contains_point((self.context_menu.x, self.context_menu.y)):
                    self.vessels.remove(v)
                    break
        elif selected_option == "Head-On Scenario":
            head_on_scenario(self, sw, sh)
        elif selected_option == "Cross Over Scenario":
            cross_over_scenario(self, sw, sh)
        elif selected_option == "Over Taking Scenario":
            over_taking_scenario(self, sw, sh)
        elif selected_option == "Multi vessel Scenario":
            multi_vessel_scenario(self, sw, sh)
        elif selected_option == "Multi vessel Scenario2":
            multi_vessel_scenario_2(self, sw, sh)

    def update_vessels(self, dt):
        # gate movement: only proceed if movement key pressed or goals queued
        if not self.movement_active and not self.goal_queue:
            return

        # advance simulation clock
        self._sim_time += dt
        if dt <= 0:
            return

        # assign all queued goals at once
        if self.goal_queue:
            for entry in self.goal_queue:
                # unpack (vessel, goal)
                if isinstance(entry, tuple) and len(entry) == 2:
                    vessel, goal = entry
                else:
                    continue
                if isinstance(vessel, int):
                    vessel = next((v for v in self.vessels if id(v) == vessel), None)
                if not vessel:
                    continue

                vessel.goal = goal

            self.goal_queue.clear()
        if not self.movement_active:
            return

        # 1) compute desired velocities
        for v in self.vessels:
            v.calculate_desired_velocity()

        # 2) detect conflicts (vessel-vessel only)
        to_query = []
        for v in self.vessels:
            conflict = False
            neigh = [o for o in self.vessels if o is not v
                     and math.hypot(v.x - o.x, v.y - o.y) / self.pixels_per_km < self.llm_trigger_distance_km]
            if neigh:
                vx, vy = v.desired_velocity
                converging = any(
                    (o.x - v.x) * (o.desired_velocity[0] - vx) +
                    (o.y - v.y) * (o.desired_velocity[1] - vy) < 0
                    for o in neigh
                )
                if converging:
                    conflict = True
                else:
                    v.current_maneuver = None
                    v.in_maneuver = False
            else:
                v.current_maneuver = None
                v.in_maneuver = False

            if conflict:
                last = self.llm_cooldown.get(id(v), 0.0)
                if self._sim_time - last >= self.llm_cooldown_duration:
                    to_query.append(v)

        # 3) query LLM for maneuvers
        if to_query:
            for v in to_query:
                self.llm_cooldown[id(v)] = self._sim_time

            prompt = generate_vessel_prompt(to_query, self.pixels_per_km)
            self._last_prompt = prompt
            print("===== Prompt Sent to DeepSeek =====")
            print(prompt)
            raw = get_llm_decision(prompt)
            self._last_response = raw
            print("Raw LLM response:", raw)
            self.llm_call_count += 1

            if raw:
                parsed = parse_llm_response_for_all(raw)
                if parsed:
                    print("Parsed maneuvers:", json.dumps(parsed, indent=2))
                    for entry in parsed:
                        for v in self.vessels:
                            if id(v) == entry['id']:
                                v.last_situation = entry.get('situation', '')
                                v.last_role = entry.get('role', '')
                                m = entry['maneuver']
                                v.current_maneuver = None if m == Maneuver.MAINTAIN_COURSE_SPEED else m
                                v.in_maneuver = (m != Maneuver.MAINTAIN_COURSE_SPEED)
                                print(f"Vessel {id(v)}: {m.name}")
                                break

        # 4) execute maneuvers or resume goal
        any_move = False
        for v in self.vessels:
            cm = getattr(v, 'current_maneuver', None)
            if cm not in (None, Maneuver.MAINTAIN_COURSE_SPEED):
                # apply maneuver exactly as given by the LLM
                v.apply_maneuver(cm, dt)
                v.update_position(dt)

                any_move = True
            else:
                if v.goal:
                    v.turn_towards_goal(dt)
                v.update_position(dt)
                if v.goal:
                    any_move = True

        self.movement_active = any_move

        if int(self._sim_time) != int(self._last_logged_time):
            for v in self.vessels:
                gx, gy = (v.goal if v.goal is not None else (None, None))
                self._log.append({
                    "time_s": self._sim_time,
                    "vessel_id": id(v),
                    "x": v.x,
                    "y": v.y,
                    "goal_x": gx,
                    "goal_y": gy,
                    "reached_goal": v.goal is None,
                    "prompt": self._last_prompt,
                    "response": self._last_response,
                    # record the Maneuver enum value and its name
                    "maneuver": v.current_maneuver if v.current_maneuver is not None else Maneuver.MAINTAIN_COURSE_SPEED,
                    "maneuver_name": (v.current_maneuver.name
                                      if v.current_maneuver is not None
                                      else Maneuver.MAINTAIN_COURSE_SPEED.name)
                })
            self._last_logged_time = self._sim_time

    def export_log(self, path):
        import csv
        fieldnames = [
            "time_s", "vessel_id", "x", "y", "goal_x", "goal_y",
            "reached_goal", "prompt", "response",
            "maneuver", "maneuver_name"
        ]
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self._log)
