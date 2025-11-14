import pygame
import time
import math
import json
import os
import csv
# --- Imports ---
from entity import Vessel, ContextMenu, font
from scenario_generator import head_on_scenario, cross_over_scenario, over_taking_scenario, multi_vessel_scenario, \
    multi_vessel_scenario_2
#from useLLm import get_llm_decision
from prompts_generator.minimal_prompt import generate_vessel_prompt
from response_parser import Maneuver, parse_llm_response_for_all

from modular_rag import ModularRAGManager

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
        self.llm_trigger_distance_km = 0.45
        self.pixels_per_km = 1000.0

        # simulation clock
        self._sim_time = 0.0
        self.llm_call_count = 0

        self._log = []
        self._last_logged_time = -1.0
        self._last_prompt = None
        self._last_response = None

        self.rag_system = ModularRAGManager()

        #Color Mapping for vessel
        self.color_map = {
            (255, 0, 0): "Red",
            (0, 0, 255): "Blue",
            (0, 255, 0): "Green",
            (255, 165, 0): "Orange",
            (128, 0, 128): "Purple",
        }

        #Directory to save screenshot
        self.take_screenshot_on_next_render = False
        self.screenshot_dir = "screenshots"
        if not os.path.exists(self.screenshot_dir):
            os.makedirs(self.screenshot_dir)

        self.llm_log_path = "llm_interactions_log.csv"
        self.llm_log_fieldnames = [
            'llm_call_id',
            'simulation_time_s',
            'involved_vessels',
            'prompt_data',
            'llm_response_json'
        ]

        # Write the header only if the file does not exist
        if not os.path.exists(self.llm_log_path):
            with open(self.llm_log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.llm_log_fieldnames)
                writer.writeheader()


    def draw(self, screen):
        # --- Part 1: Draw the vessels and context menu (this is the same) ---
        for vessel in self.vessels:
            vessel.draw(screen)
        if self.context_menu:
            self.context_menu.draw(screen)

        # --- Part 2: Draw the new status box ---
        if not self.vessels:
            return  # Don't draw the box if there are no vessels

        # Box settings
        box_width = 350
        box_height = 40 + (len(self.vessels) * 25)  # Dynamically adjust height
        box_padding = 10
        box_x = screen.get_width() - box_width - box_padding
        box_y = box_padding

        # Draw the box background and border
        pygame.draw.rect(screen, (220, 220, 220), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, (0, 0, 0), (box_x, box_y, box_width, box_height), 2)

        # Draw the title
        title_surface = font.render("Vessel Actions", True, (0, 0, 0))
        screen.blit(title_surface, (box_x + box_padding, box_y + box_padding))

        # Draw the status for each vessel
        for i, vessel in enumerate(self.vessels):
            # Determine the maneuver name
            maneuver = vessel.current_maneuver or Maneuver.MAINTAIN_COURSE_SPEED
            maneuver_name = maneuver.name

            # Get the color name from our map
            color_name = self.color_map.get(vessel.color, "Unknown Color")

            # Create the text string
            status_text = f"{color_name} Vessel: {maneuver_name}"

            # Render the text with the vessel's actual color
            text_surface = font.render(status_text, True, vessel.color)

            # Calculate the Y position for this line of text
            text_y = box_y + 40 + (i * 25)

            # Draw the text inside the box
            screen.blit(text_surface, (box_x + box_padding, text_y))


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
            self.movement_active = True
        elif selected_option == "Cross Over Scenario":
            cross_over_scenario(self, sw, sh)
            self.movement_active = True
        elif selected_option == "Over Taking Scenario":
            over_taking_scenario(self, sw, sh)
            self.movement_active = True
        elif selected_option == "Multi vessel Scenario":
            multi_vessel_scenario(self, sw, sh)
            self.movement_active = True
        elif selected_option == "Multi vessel Scenario2":
            multi_vessel_scenario_2(self, sw, sh)
            self.movement_active = True

    def predict_collision(self, v1, v2, time_horizon_sec=60.0, min_dist_km=0.1):
        """
        Predicts if two vessels will come within a minimum distance in a future time horizon.
        Returns True if a potential collision is detected, otherwise False.
        """
        # Relative position (vector from v2 to v1)
        p_rel_x = v1.x - v2.x
        p_rel_y = v1.y - v2.y

        # Relative velocity (vector of v1's velocity relative to v2)
        v_rel_x = v1.desired_velocity[0] - v2.desired_velocity[0]
        v_rel_y = v1.desired_velocity[1] - v2.desired_velocity[1]

        # Magnitude of relative velocity squared
        v_rel_mag_sq = v_rel_x ** 2 + v_rel_y ** 2
        if v_rel_mag_sq == 0:
            return False  # Vessels are moving parallel at the same speed

        # Time to closest point of approach (TCPA)
        # This is derived from the dot product of relative position and relative velocity
        dot_product = (p_rel_x * v_rel_x) + (p_rel_y * v_rel_y)
        tcpa = -dot_product / v_rel_mag_sq

        # We only care about future collisions
        if not (0 < tcpa < time_horizon_sec):
            return False

        # Distance at closest point of approach (DCPA)
        # Calculate the positions at TCPA
        future_x1 = v1.x + v1.desired_velocity[0] * tcpa
        future_y1 = v1.y + v1.desired_velocity[1] * tcpa
        future_x2 = v2.x + v2.desired_velocity[0] * tcpa
        future_y2 = v2.y + v2.desired_velocity[1] * tcpa

        dist_sq = (future_x1 - future_x2) ** 2 + (future_y1 - future_y2) ** 2
        dcpa_km = math.sqrt(dist_sq) / self.pixels_per_km

        # If the distance at the closest point is less than our minimum safe distance, it's a conflict
        if dcpa_km < min_dist_km:
            #print(f"PREDICTED COLLISION between Vessel {id(v1)} and {id(v2)}! TCPA: {tcpa:.1f}s, DCPA: {dcpa_km:.3f}km")
            return True

        return False

        # In entity_manager.py, add this new method inside the EntityManager class

    def log_llm_interaction(self, to_query_vessels, prompt, response_json):
        """
        Logs the details of a single LLM interaction to a CSV file.
        """
        # Create a descriptive string for the vessels involved in this query
        vessel_details = []
        for v in to_query_vessels:
            color_name = self.color_map.get(v.color, "Unknown")
            vessel_details.append(f"{color_name} (ID: {id(v)})")
        involved_str = ", ".join(vessel_details)

        # Prepare the data row as a dictionary
        log_entry = {
            'llm_call_id': self.llm_call_count,
            'simulation_time_s': f"{self._sim_time:.2f}",
            'involved_vessels': involved_str,
            'prompt_data': prompt,
            'llm_response_json': response_json
        }

        # Open the file in append mode and write the new row
        try:
            with open(self.llm_log_path, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.llm_log_fieldnames)
                writer.writerow(log_entry)
            print(f"--- LLM interaction {self.llm_call_count} logged to {self.llm_log_path} ---")
        except Exception as e:
            print(f"ERROR: Could not write to LLM log file: {e}")

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
        MOVING_THRESHOLD_KMPH = 0.1
        for v in self.vessels:
            # Skip vessels that are not moving
            speed_kmh = (v.speed / self.pixels_per_km) * 3600
            if speed_kmh <= MOVING_THRESHOLD_KMPH:
                v.current_maneuver = None
                v.in_maneuver = False
                continue

            conflict_found = False
            # Check for potential future collisions with every other moving vessel
            for other_vessel in self.vessels:
                if v is other_vessel:
                    continue

                other_speed_kmh = (other_vessel.speed / self.pixels_per_km) * 3600
                if other_speed_kmh <= MOVING_THRESHOLD_KMPH:
                    continue

                # Use predictive function
                if self.predict_collision(v, other_vessel):
                    conflict_found = True
                    break  # Found a conflict for this vessel, no need to check others

            # If no conflict was predicted, reset the vessel's maneuver state
            # if not conflict_found:
            #     last_query_time = self.llm_cooldown.get(id(v), -1000) # Get last query time
            #     # Small buffer to the cooldown duration
            #     if self._sim_time - last_query_time > self.llm_cooldown_duration + 2.0:
            #         v.current_maneuver = None
            #         v.in_maneuver = False
            #
            # # If there is a conflict and the vessel is not on cooldown, add to query list
            # if conflict_found:
            #     last = self.llm_cooldown.get(id(v), 0.0)
            #     if self._sim_time - last >= self.llm_cooldown_duration:
            #         to_query.append(v)

            # Set the vessel's maneuver state based ONLY on the prediction
            v.in_maneuver = conflict_found

            # If there is a conflict and the vessel is not on cooldown, add to query list
            if conflict_found:
                last = self.llm_cooldown.get(id(v), 0.0)
                if self._sim_time - last >= self.llm_cooldown_duration:
                    to_query.append(v)
            # If no conflict is found, we can clear any specific maneuver command
            else:
                v.current_maneuver = None

        # 3) query LLM for maneuvers
        did_llm = False
        if to_query:
            did_llm = True
            for v in to_query:
                self.llm_cooldown[id(v)] = self._sim_time

            prompt = generate_vessel_prompt(to_query, self.pixels_per_km)
            self._last_prompt = prompt
            print("===== Prompt Sent to LLM =====")
            # print(prompt)
            raw = self.rag_system.get_llm_decision(prompt)
            #raw = get_llm_decision(prompt)
            self._last_response = raw
            print("Raw LLM response:", raw)
            self.llm_call_count += 1

            # --- TAKE SCREENSHOT FALG TRUE AFTER LLM CALL ---
            self.take_screenshot_on_next_render = True
            # --- END OF SECTION ---
            # Call the new logging function here
            if raw:
                self.log_llm_interaction(to_query, prompt, raw)

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
                                # Set the specific command, or None if it's just to maintain
                                v.current_maneuver = m if m != Maneuver.MAINTAIN_COURSE_SPEED else None
                                print(f"Vessel {id(v)}: {m.name}")
                                break

        # 4) execute maneuvers or resume goal
        any_move = False
        for v in self.vessels:
            # If the vessel is in an avoidance state:
            if v.in_maneuver:
                # If there's a specific action command, apply it
                if v.current_maneuver:
                    v.apply_maneuver(v.current_maneuver, dt)
                # If the command is MAINTAIN, it does nothing here,
                # so it will continue on its last heading.

            # Otherwise, if it's not in a maneuver, head for the goal
            else:
                if v.goal:
                    v.turn_towards_goal(dt)

            # Update position regardless of state
            v.update_position(dt)

            # Check if the vessel has reached its goal
            if v.goal is None:
                v.current_maneuver = None
                v.in_maneuver = False
                v.speed = 0

            # Determine if any vessel is still active
            if v.goal or v.speed > 0:
                any_move = True

        if did_llm or int(self._sim_time) != int(self._last_logged_time):
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
                    "prompt": self._last_prompt if did_llm else "",
                    "response": self._last_response if did_llm else "",
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
