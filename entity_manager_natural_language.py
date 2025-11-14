import pygame
import time
import collections
import math
import json
import os
import csv
# --- Imports ---
from entity import Vessel, ContextMenu, font, Francisco
from scenario_generator import (head_on_scenario, cross_over_scenario,
                                over_taking_scenario, multi_vessel_scenario,
                                multi_vessel_scenario_2, traffic_separation_scenario)

from vision_manager import VisionDecisionManager
# We only import the two prompt generators this manager will use
from prompts_generator.natural_language_prompt import generate_natural_language_prompt
from prompts_generator.tss_prompt import generate_tss_crossing_prompt
from response_parser import Maneuver, parse_llm_response_for_all


class EntityManager:
    """
    EXPERIMENTAL: This EntityManager uses a HYBRID + NATURAL LANGUAGE approach.
    - For TSS, it uses the specific tss_prompt.
    - For all other scenarios, it uses the natural_language_prompt.
    """

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.vessels = []
        self.context_menu = None
        self.movement_active = False
        self.goal_queue = []

        self.llm_cooldown = {}
        self.llm_cooldown_duration = 4.0
        self.pixels_per_km = 1000.0
        self.radar_range_km = 0.3  # Tunable radar range
        self._sim_time = 0.0
        self.llm_call_count = 0
        self._last_response = None

        self.max_history_length = 3
        self.history_vessel_data = collections.deque(maxlen=self.max_history_length)
        self.history_responses = collections.deque(maxlen=self.max_history_length)

        self.vision_system = VisionDecisionManager()
        self.current_scenario = None

        self.color_map = {
            (255, 0, 0): "Red", (0, 0, 255): "Blue", (0, 255, 0): "Green",
            (255, 165, 0): "Orange", (128, 0, 128): "Purple",
        }

        self.take_screenshot_on_next_render = False
        self.screenshot_dir = "screenshots_natural"
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

        self.llm_log_path = "llm_natural_interactions_log.csv"
        self.llm_log_fieldnames = ['llm_call_id', 'simulation_time_s', 'involved_vessels', 'prompt_data',
                                   'llm_response_json']
        if not os.path.exists(self.llm_log_path):
            with open(self.llm_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.llm_log_fieldnames)
                writer.writeheader()

    def draw(self, screen):
        for vessel in self.vessels:
            vessel.draw(screen)
        if self.context_menu:
            self.context_menu.draw(screen)
        if not self.vessels:
            return


    def show_context_menu(self, pos, options):  # Unchanged
        self.context_menu = ContextMenu(pos[0], pos[1], options)

    def add_vessel(self, vessel):  # Unchanged
        self.vessels.append(vessel)

    def handle_context_selection(self, selected_option):
        sw = self.game_manager.graphics_manager.width
        sh = self.game_manager.graphics_manager.height
        cx = self.context_menu.x + self.context_menu.width // 2
        cy = self.context_menu.y + self.context_menu.height // 2

        # --- Helper function to clear history ---
        def _clear_history():
            print("--- New scenario selected. Clearing LLM history. ---")
            self.history_vessel_data.clear()
            self.history_responses.clear()

        # --- End helper ---

        if selected_option == "Create Vessel":
            self.add_vessel(Vessel(cx, cy, self.pixels_per_km))
        elif selected_option == "Delete Vessel":
            for v in list(self.vessels):
                if v.contains_point((self.context_menu.x, self.context_menu.y)): self.vessels.remove(v); break
        elif selected_option == "Head-On Scenario":
            _clear_history()  # <-- CLEAR HISTORY
            self.current_scenario = "head_on"
            head_on_scenario(self, sw, sh);
            self.movement_active = True
        elif selected_option == "Cross Over Scenario":
            _clear_history()  # <-- CLEAR HISTORY
            self.current_scenario = "cross_over"
            cross_over_scenario(self, sw, sh);
            self.movement_active = True
        elif selected_option == "Over Taking Scenario":
            _clear_history()  # <-- CLEAR HISTORY
            self.current_scenario = "over_taking"
            over_taking_scenario(self, sw, sh);
            self.movement_active = True
        elif selected_option == "Multi vessel Scenario":
            _clear_history()  # <-- CLEAR HISTORY
            self.current_scenario = "multi_vessel"
            multi_vessel_scenario(self, sw, sh);
            self.movement_active = True
        elif selected_option == "Multi vessel Scenario2":
            _clear_history()  # <-- CLEAR HISTORY
            self.current_scenario = "multi_vessel_2"
            multi_vessel_scenario_2(self, sw, sh);
            self.movement_active = True
        elif selected_option == "Traffic Separation Scenario":
            _clear_history()  # <-- CLEAR HISTORY
            self.current_scenario = "tss"
            traffic_separation_scenario(self, sw, sh)
            self.movement_active = True

    def predict_collision(self, v1, v2, time_horizon_sec=60.0, min_dist_km=0.1):  # Unchanged
        # ... (This method is unchanged, copy your version here) ...
        p_rel_x = v1.x - v2.x;
        p_rel_y = v1.y - v2.y
        v_rel_x = v1.desired_velocity[0] - v2.desired_velocity[0];
        v_rel_y = v1.desired_velocity[1] - v2.desired_velocity[1]
        v_rel_mag_sq = v_rel_x ** 2 + v_rel_y ** 2
        if v_rel_mag_sq == 0: return False
        dot_product = (p_rel_x * v_rel_x) + (p_rel_y * v_rel_y)
        tcpa = -dot_product / v_rel_mag_sq
        if not (0 < tcpa < time_horizon_sec): return False
        future_x1 = v1.x + v1.desired_velocity[0] * tcpa;
        future_y1 = v1.y + v1.desired_velocity[1] * tcpa
        future_x2 = v2.x + v2.desired_velocity[0] * tcpa;
        future_y2 = v2.y + v2.desired_velocity[1] * tcpa
        dist_sq = (future_x1 - future_x2) ** 2 + (future_y1 - future_y2) ** 2
        dcpa_km = math.sqrt(dist_sq) / self.pixels_per_km
        if dcpa_km < min_dist_km: return True
        return False

    def log_llm_interaction(self, to_query_vessels, prompt, response_json):  # Unchanged
        # ... (This method is unchanged, copy your version here) ...
        vessel_details = []
        for v in to_query_vessels:
            color_name = self.color_map.get(v.color, "Unknown")
            vessel_details.append(f"{color_name} (ID: {id(v)})")
        involved_str = ", ".join(vessel_details)
        log_entry = {
            'llm_call_id': self.llm_call_count, 'simulation_time_s': f"{self._sim_time:.2f}",
            'involved_vessels': involved_str, 'prompt_data': prompt, 'llm_response_json': response_json
        }
        try:
            with open(self.llm_log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.llm_log_fieldnames)
                writer.writerow(log_entry)
            print(f"--- LLM interaction {self.llm_call_count} logged to {self.llm_log_path} ---")
        except Exception as e:
            print(f"ERROR: Could not write to LLM log file: {e}")

    async def update_vessels(self, dt):
        # ... (Start of method, goal queue, heading/speed/position update... all unchanged) ...
        if not self.movement_active and not self.goal_queue: return
        self._sim_time += dt
        if dt <= 0: return
        if self.goal_queue:
            for entry in self.goal_queue:
                if isinstance(entry, tuple) and len(entry) == 2:
                    vessel, goal = entry
                else:
                    continue
                if isinstance(vessel, int): vessel = next((v for v in self.vessels if id(v) == vessel), None)
                if not vessel: continue
                vessel.goal = goal
            self.goal_queue.clear()
        if not self.movement_active: return
        any_move = False
        for v in self.vessels:
            is_tss = (self.current_scenario == 'tss' and isinstance(v, Francisco))
            v.update_heading_and_speed(dt, is_tss)
            v.update_position(dt)
            if v.goal is None and not v.in_maneuver and v.speed < 0.1: v.speed = 0
            if v.goal or v.speed > 0.1: any_move = True
        self.movement_active = any_move

        # ... (Calculate velocities and detect conflicts logic is unchanged) ...
        for v in self.vessels: v.calculate_desired_velocity()
        to_query = []
        MOVING_THRESHOLD_KMPH = 0.1
        for v in self.vessels:
            speed_kmh = (v.speed / self.pixels_per_km) * 3600
            if speed_kmh <= MOVING_THRESHOLD_KMPH: v.in_maneuver = False; continue
            conflict_found = False
            for other_vessel in self.vessels:
                if v is other_vessel: continue
                other_speed_kmh = (other_vessel.speed / self.pixels_per_km) * 3600
                if other_speed_kmh <= MOVING_THRESHOLD_KMPH: continue
                current_dist_km = math.hypot(v.x - other_vessel.x, v.y - other_vessel.y) / self.pixels_per_km
                if current_dist_km > self.radar_range_km: continue
                if self.predict_collision(v, other_vessel): conflict_found = True; break
            if conflict_found:
                v.in_maneuver = True
                if self.current_scenario == 'tss':
                    if isinstance(v, Francisco):
                        if self._sim_time - self.llm_cooldown.get(id(v), 0.0) >= self.llm_cooldown_duration:
                            to_query.append(v)
                else:
                    if self._sim_time - self.llm_cooldown.get(id(v), 0.0) >= self.llm_cooldown_duration:
                        to_query.append(v)
            else:
                last_query_time = self.llm_cooldown.get(id(v), -999)
                grace_period = self.llm_cooldown_duration + 5.0
                if self._sim_time - last_query_time > grace_period:
                    v.in_maneuver = False
                    v.current_maneuver = None

        # 3) query LLM for maneuvers
        if to_query:
            for v in to_query: self.llm_cooldown[id(v)] = self._sim_time
            context_vessels = set(to_query)
            for vessel_in_query in to_query:
                for other_vessel in self.vessels:
                    if vessel_in_query is not other_vessel and self.predict_collision(vessel_in_query, other_vessel):
                        context_vessels.add(other_vessel)
            current_vessel_states = []
            for v_ctx in context_vessels:
                current_vessel_states.append({
                    "id": id(v_ctx), "pos": (f"{v_ctx.x:.1f}", f"{v_ctx.y:.1f}"),
                    "heading_deg": f"{math.degrees(v_ctx.heading):.1f}",
                    "speed_kmh": f"{(v_ctx.speed / self.pixels_per_km * 3600):.1f}"
                })
            prompt_history_data = list(self.history_vessel_data)
            response_history_data = list(self.history_responses)

            # ---  PROMPT SELECTION LOGIC ---
            text_prompt_for_llm = ""
            if self.current_scenario == 'tss':
                print(
                    f"===== Generating TSS-specific prompt with history (last {len(prompt_history_data)} steps)... =====")
                text_prompt_for_llm = generate_tss_crossing_prompt(
                    to_query, list(context_vessels), self.pixels_per_km,
                    previous_vessel_data_list=prompt_history_data,
                    previous_responses=response_history_data
                )
            else:
                # This is the "natural language" manager, so the default case
                # should be the natural language prompt.
                print(
                    f"===== Generating NATURAL LANGUAGE prompt with history (last {len(prompt_history_data)} steps)... =====")
                text_prompt_for_llm = generate_natural_language_prompt(
                    to_query,
                    list(context_vessels),
                    self.pixels_per_km,
                    previous_vessel_data_list=prompt_history_data,
                    previous_responses=response_history_data
                )

            # ... LLM call, logging, parsing, storing history) ...
            print("===== Calling Vision LLM with Image AND Text Prompt... =====")
            raw = await self.vision_system.get_llm_decision_from_image(self.game_manager.graphics_manager.screen,
                                                                       text_prompt_for_llm)
            self._last_response = raw
            print("Raw LLM response:", raw)
            self.llm_call_count += 1
            self.take_screenshot_on_next_render = True
            if raw:
                self.log_llm_interaction(to_query, text_prompt_for_llm, raw)
                parsed = parse_llm_response_for_all(raw)
                if parsed:
                    self.history_vessel_data.append(current_vessel_states)
                    self.history_responses.append(parsed)
                    print("\n--- FINAL PARSED ACTIONS ---")
                    for entry in parsed:
                        vessel_to_update = next((v for v in self.vessels if id(v) == entry['id']), None)
                        if vessel_to_update:
                            vessel_to_update.last_situation = entry.get('situation', '')
                            vessel_to_update.last_role = entry.get('role', '')
                            maneuver_enum = entry['maneuver']
                            vessel_to_update.set_maneuver(maneuver_enum)
                            color_name = self.color_map.get(vessel_to_update.color, "Unknown")
                            print(
                                f"  > {color_name} Vessel (ID: {entry['id']}): Assigned Maneuver -> {maneuver_enum.name}")
                    print("--------------------------\n")