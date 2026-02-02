import pygame
import collections
import math
import os
import csv
import asyncio
from typing import List

# --- Imports ---
from entity import Vessel, Francisco
from scenario_generator import (head_on_scenario, cross_over_scenario,
                                over_taking_scenario, multi_vessel_scenario,
                                multi_vessel_scenario_2, traffic_separation_scenario)
from response_parser import Maneuver, parse_llm_response_for_all
from llm_text_manager import LLMTextManager

import prompts_generator.natural_language_prompt as natural_gen
import prompts_generator.tss_prompt as tss_gen


class EntityManager:
    def __init__(self, game_manager, llm_provider='openai'):
        self.game_manager = game_manager
        self.vessels: List[Vessel] = []
        self.movement_active = False
        self.current_scenario = "none"
        self._sim_time = 0.0
        self.llm_cooldown = {}
        self.llm_cooldown_duration = 5.0
        self.pixels_per_km = 1000.0
        self.radar_range_km = 0.8
        self.llm_call_count = 0
        self.max_history_length = 3
        self.history_vessel_data = collections.deque(maxlen=self.max_history_length)
        self.history_responses = collections.deque(maxlen=self.max_history_length)
        self.text_system = LLMTextManager(provider=llm_provider)

        self.llm_log_path = "logs/llm_text_history_log.csv"
        self.llm_log_fieldnames = ['llm_call_id', 'simulation_time_s', 'scenario', 'prompt_type',
                                   'involved_vessels', 'explanation', 'prompt_data', 'llm_response_json']
        os.makedirs(os.path.dirname(self.llm_log_path), exist_ok=True)
        if not os.path.exists(self.llm_log_path):
            with open(self.llm_log_path, 'w', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=self.llm_log_fieldnames).writeheader()

        self.color_map = {(255, 0, 0): "Red", (0, 0, 255): "Blue", (0, 255, 0): "Green",
                          (255, 165, 0): "Orange", (128, 0, 128): "Purple"}

    def load_scenario(self, selected_option):
        self.vessels.clear();
        self.history_vessel_data.clear();
        self.history_responses.clear()
        self._sim_time = 0.0;
        self.llm_call_count = 0
        sw, sh = self.game_manager.graphics_manager.width, self.game_manager.graphics_manager.height
        scenarios = {
            "Head-On Scenario": ("head_on", head_on_scenario),
            "Cross Over Scenario": ("cross_over", cross_over_scenario),
            "Over Taking Scenario": ("over_taking", over_taking_scenario),
            "Multi vessel Scenario": ("multi_vessel", multi_vessel_scenario),
            "Multi vessel Scenario2": ("multi_vessel_2", multi_vessel_scenario_2),
            "Traffic Separation Scenario": ("tss", traffic_separation_scenario)
        }
        if selected_option in scenarios:
            self.current_scenario, func = scenarios[selected_option]
            func(self, sw, sh);
            self.movement_active = True

    def predict_collision(self, v1, v2, time_horizon_sec=60.0, min_dist_km=0.15):
        p_rel_x, p_rel_y = v1.x - v2.x, v1.y - v2.y
        v_rel_x, v_rel_y = v1.desired_velocity[0] - v2.desired_velocity[0], v1.desired_velocity[1] - \
                           v2.desired_velocity[1]
        v_rel_mag_sq = v_rel_x ** 2 + v_rel_y ** 2
        if v_rel_mag_sq == 0: return False
        tcpa = -(p_rel_x * v_rel_x + p_rel_y * v_rel_y) / v_rel_mag_sq
        if not (0 < tcpa < time_horizon_sec): return False
        dist = math.hypot(p_rel_x + v_rel_x * tcpa, p_rel_y + v_rel_y * tcpa) / self.pixels_per_km
        return dist < min_dist_km

    async def update_vessels(self, dt):
        if not self.movement_active: return
        self._sim_time += dt
        for v in self.vessels:
            is_tss = (self.current_scenario == 'tss' and isinstance(v, Francisco))
            v.update_heading_and_speed(dt, is_tss);
            v.update_position(dt);
            v.calculate_desired_velocity()

        to_query = []
        for v in self.vessels:
            if v.speed < 0.1: continue
            conflict = False
            for o in self.vessels:
                if v is o: continue
                if math.hypot(v.x - o.x,
                              v.y - o.y) / self.pixels_per_km < self.radar_range_km and self.predict_collision(v, o):
                    conflict = True;
                    break
            if conflict:
                v.in_maneuver = True
                if self._sim_time - self.llm_cooldown.get(id(v), 0) >= self.llm_cooldown_duration:
                    if self.current_scenario != 'tss' or isinstance(v, Francisco): to_query.append(v)
            else:
                last_call = self.llm_cooldown.get(id(v), -999)
                if self._sim_time - last_call > (self.llm_cooldown_duration + 2.0):
                    v.in_maneuver = False;
                    v.current_maneuver = None

        if to_query: await self._handle_decision(to_query)

    async def _handle_decision(self, to_query):
        for v in to_query: self.llm_cooldown[id(v)] = self._sim_time
        context = set(to_query)
        for v in to_query:
            for o in self.vessels:
                if v is not o and self.predict_collision(v, o): context.add(o)

        curr_states = [
            {"id": id(v), "pos": (f"{v.x:.1f}", f"{v.y:.1f}"), "heading_deg": f"{math.degrees(v.heading):.1f}",
             "speed_kmh": f"{(v.speed / self.pixels_per_km * 3600):.1f}"} for v in context]

        prompt_type = self.game_manager.ui_manager.get_value("prompt")
        if self.current_scenario == 'tss':
            prompt = tss_gen.generate_tss_crossing_prompt(to_query, list(context), self.pixels_per_km,
                                                          list(self.history_vessel_data), list(self.history_responses))
            actual_p = "tss"
        else:
            prompt = natural_gen.generate_natural_language_prompt(to_query, list(context), self.pixels_per_km,
                                                                  list(self.history_vessel_data),
                                                                  list(self.history_responses))
            actual_p = f"natural_with_history"

        # --- DEBUG VISUALIZATION ---
        print(f"\n{'=' * 20} LEVEL 2: TEMPORAL {'=' * 20}")
        print(f"HISTORY STEPS IN MEMORY: {len(self.history_vessel_data)}")
        print("-" * 50);
        print(prompt);
        print("-" * 50)

        raw = self.text_system.get_llm_decision_standard(prompt)
        print(f"RAW RESPONSE: {raw}")

        if raw:
            self.llm_call_count += 1
            parsed = parse_llm_response_for_all(raw)
            self._log_interaction(to_query, prompt, raw, parsed, actual_p)
            if parsed:
                self.history_vessel_data.append(curr_states)
                self.history_responses.append(parsed)
                for entry in parsed:
                    v_upd = next((x for x in self.vessels if id(x) == entry['id']), None)
                    if v_upd:
                        v_upd.set_maneuver(entry['maneuver'])
                        print(f"ACTION -> {self.color_map.get(v_upd.color)}: {entry['maneuver'].name}")
        print(f"{'=' * 50}\n")

    def _log_interaction(self, vessels, prompt, raw, parsed, p_type):
        v_str = ", ".join([f"{self.color_map.get(v.color, '?')}({id(v)})" for v in vessels])
        exp_str = " | ".join([
                                 f"[{self.color_map.get(next((v.color for v in self.vessels if id(v) == p['id']), (0, 0, 0)), '?')}]: {p.get('explanation', 'N/A')}"
                                 for p in parsed])
        entry = {'llm_call_id': self.llm_call_count, 'simulation_time_s': f"{self._sim_time:.2f}",
                 'scenario': self.current_scenario, 'prompt_type': p_type, 'involved_vessels': v_str,
                 'explanation': exp_str, 'prompt_data': prompt, 'llm_response_json': raw}
        with open(self.llm_log_path, 'a', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=self.llm_log_fieldnames).writerow(entry)

    def draw(self, screen):
        for v in self.vessels: v.draw(screen)