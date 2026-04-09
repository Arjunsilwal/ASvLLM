import pygame
import collections
import math
import os
import csv
import asyncio
import re
from typing import List

from entity import Vessel, Francisco
from scenario_generator import (head_on_scenario, cross_over_scenario,
                                over_taking_scenario, multi_vessel_scenario,
                                multi_vessel_scenario_2, multi_vessel_scenario_3,
                                traffic_separation_scenario)
from response_parser import parse_llm_response_for_all
from llm_text_manager import LLMTextManager

import prompts_generator.minimal_prompt as minimal_gen
import prompts_generator.moderate_prompt as moderate_gen
import prompts_generator.detailed_prompt as detailed_gen
import prompts_generator.natural_language_prompt as natural_gen
import prompts_generator.tss_prompt as tss_gen


class EntityManager:
    def __init__(self, game_manager, llm_provider='openai'):
        self.game_manager = game_manager
        self.llm_provider = llm_provider
        self.vessels: List[Vessel] = []
        self.movement_active = False
        self.current_scenario = "none"
        self._sim_time = 0.0
        self.llm_cooldown = {}
        self.llm_cooldown_duration = 5.0
        self.pixels_per_km = 1000.0
        self.radar_range_km = 0.8
        self.llm_call_count = 0
        self.decision_maker = LLMTextManager(provider=llm_provider)
        self.is_ai_thinking = False

        self.llm_log_path = f"logs/results_standard_{llm_provider}.csv"
        self.llm_log_fieldnames = ['Experiment ID', 'Call ID', 'Scenario', 'Mode', 'LLM Provider', 'Prompt Type',
                                   'Involved Vessels', 'Ground Truth (Prompt)', 'GT Rule', 'LLM Action',
                                   'LLM Cited Rule', 'LLM Explanation Logic', 'Verdict', 'llm_response_json']
        os.makedirs("logs", exist_ok=True)
        if not os.path.exists(self.llm_log_path):
            with open(self.llm_log_path, 'w', newline='', encoding='utf-8') as f:
                csv.DictWriter(f, fieldnames=self.llm_log_fieldnames).writeheader()
        self.color_map = {(255, 0, 0): "Red", (0, 0, 255): "Blue", (0, 255, 0): "Green", (255, 165, 0): "Orange",
                          (128, 0, 128): "Purple"}

    def add_vessel(self, vessel):
        self.vessels.append(vessel)

    async def update_vessels(self, dt):
        if not self.movement_active: return
        self._sim_time += dt
        is_tss = self.current_scenario in ["tss", "Traffic Separation Scenario"]

        for v in self.vessels:
            v.update_heading_and_speed(dt, is_tss)
            v.update_position(dt)

        if self.is_ai_thinking: return
        to_query = []
        for v in self.vessels:
            if v.speed < 0.1 or v.reached_goal or v.in_maneuver: continue
            if is_tss and not isinstance(v, Francisco): continue

            conflict = False
            for o in self.vessels:
                if v is o or o.reached_goal: continue
                if self.predict_collision(v, o): conflict = True; break

            if conflict:
                v.selected = True
                if (self._sim_time - self.llm_cooldown.get(id(v), 0) >= self.llm_cooldown_duration): to_query.append(v)
            else:
                v.selected = False

        if to_query: asyncio.create_task(self._handle_ai_decision(to_query))

    async def _handle_ai_decision(self, to_query):
        self.is_ai_thinking = True
        try:
            for v in to_query: self.llm_cooldown[id(v)] = self._sim_time
            context = set(to_query)
            for v in to_query:
                for o in self.vessels:
                    if v is not o and self.predict_collision(v, o): context.add(o)

            curr_states = [
                {"id": id(v), "pos": (f"{v.x:.1f}", f"{v.y:.1f}"), "heading_deg": f"{math.degrees(v.heading):.1f}",
                 "speed_kmh": f"{(v.speed / self.pixels_per_km * 3600):.1f}"} for v in context]

            p_type = self.game_manager.current_prompt_type or self.game_manager.ui_manager.get_value(
                "prompt") or "natural"
            if self.current_scenario in ['Traffic Separation Scenario', 'tss'] or p_type == "tss":
                prompt = tss_gen.generate_tss_crossing_prompt(to_query, list(context), self.pixels_per_km)
                actual_p = "tss"
            else:
                actual_p = p_type
                if p_type == 'minimal':
                    prompt = minimal_gen.generate_vessel_prompt(to_query, list(context), self.pixels_per_km)
                elif p_type == 'moderate':
                    prompt = moderate_gen.generate_vessel_prompt(to_query, list(context), self.pixels_per_km)
                elif p_type == 'detailed':
                    prompt = detailed_gen.generate_vessel_prompt(to_query, list(context), self.pixels_per_km)
                else:
                    prompt = natural_gen.generate_natural_language_prompt(to_query, list(context), self.pixels_per_km)

            raw = await self.decision_maker.get_llm_decision_standard(prompt)
            if raw:
                self.llm_call_count += 1
                parsed = parse_llm_response_for_all(raw)
                self._log_interaction(to_query, prompt, raw, parsed, actual_p)
                for entry in parsed:
                    v_upd = next((x for x in self.vessels if id(x) == entry['id']), None)
                    if v_upd: v_upd.set_maneuver(entry['maneuver'])
        finally:
            self.is_ai_thinking = False

    def _evaluate_verdict(self, gt_rule: str, llm_action: str, is_tss: bool) -> str:
        action = llm_action.lower()

        if is_tss:
            # For TSS, efficiency (acceleration) or safety (starboard/reduce) are all Pass.
            # Only an unsafe "Alter course to port" into traffic would be a clear Fail.
            return "Fail" if "port" in action and "starboard" not in action else "Pass"

        if "rule 14" in gt_rule.lower():
            # Rule 14: Both must alter to starboard
            return "Pass" if "starboard" in action else "Fail"
        elif "crossing-stbd" in gt_rule.lower():
            # We are Give-way: Must take early action (Starboard, Astern, or Reduce)
            return "Pass" if any(x in action for x in ["starboard", "astern", "reduce", "slow"]) else "Fail"
        elif "crossing-port" in gt_rule.lower():
            # We are Stand-on: Must maintain course and speed
            # Exception: Rule 17 allows action if collision is imminent, but for sims, Maintain is the gold standard.
            return "Pass" if "maintain" in action or "keep" in action else "Fail"
        elif "overtaking" in gt_rule.lower():
            # We are Overtaking: Must keep clear (any direction or speed change)
            return "Pass" if any(x in action for x in ["starboard", "port", "reduce", "slow"]) else "Fail"

        return "Manual"

    def _log_interaction(self, vessels, prompt, raw, parsed, p_type):
        is_tss = self.current_scenario in ["tss", "Traffic Separation Scenario"]
        actions, explanations, cited_rules, gt_rules, verdicts = [], [], [], [], []
        v_str = ", ".join([f"{self.color_map.get(v.color, '?')}({id(v)})" for v in vessels])
        for v in vessels:
            v_color = self.color_map.get(v.color, '?')
            gt_rule = "Rule 10 (TSS)" if is_tss else "Clear"

            # FIX: Added parentheses to ensure threats is assigned the list, not the boolean result of 'and'
            if (threats := [o for o in self.vessels if o is not v and o.speed > 0.1]) and not is_tss:
                closest = min(threats, key=lambda o: math.hypot(v.x - o.x, v.y - o.y))
                gt_rule = self._calculate_ground_truth_rule(v, closest)
            gt_rules.append(f"[{v_color}]: {gt_rule}")

            p = next((item for item in parsed if item['id'] == id(v)), None)
            if p:
                actions.append(f"[{v_color}]: {p.get('action', 'N/A')}")
                explanations.append(f"[{v_color}]: {p.get('explanation', 'N/A')}")
                verdicts.append(f"[{v_color}]: {self._evaluate_verdict(gt_rule, p.get('action', ''), is_tss)}")
                # REGEX FIX: Catch R15, Rule 15, etc.
                match = re.search(r"(?:Rule\s*|R)(\d+)", str(p.get('explanation', '')), re.IGNORECASE)
                cited_rules.append(f"[{v_color}]: {match.group(0) if match else 'None'}")

        entry = {
            'Experiment ID': self.game_manager.current_experiment_id, 'Call ID': self.llm_call_count,
            'Scenario': self.current_scenario,
            'Mode': "standard", 'LLM Provider': self.llm_provider, 'Prompt Type': p_type,
            'Involved Vessels': v_str, 'Ground Truth (Prompt)': prompt, 'GT Rule': " | ".join(gt_rules),
            'LLM Action': " | ".join(actions),
            'LLM Cited Rule': " | ".join(cited_rules), 'LLM Explanation Logic': " | ".join(explanations),
            'Verdict': " | ".join(verdicts), 'llm_response_json': raw
        }
        with open(self.llm_log_path, 'a', newline='', encoding='utf-8') as f:
            csv.DictWriter(f, fieldnames=self.llm_log_fieldnames).writerow(entry)

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

    def load_scenario(self, selected_option):
        self.vessels.clear();
        self._sim_time = 0.0;
        self.llm_call_count = 0
        sw, sh = self.game_manager.graphics_manager.width, self.game_manager.graphics_manager.height
        scenarios = {
            "Head-On Scenario": head_on_scenario, "Cross Over Scenario": cross_over_scenario,
            "Over Taking Scenario": over_taking_scenario, "Multi vessel Scenario": multi_vessel_scenario,
            "Multi vessel Scenario 2": multi_vessel_scenario_2, "Multi vessel Scenario 3": multi_vessel_scenario_3,
            "Traffic Separation Scenario": traffic_separation_scenario
        }
        if selected_option in scenarios:
            self.current_scenario = selected_option
            scenarios[selected_option](self, sw, sh);
            self.movement_active = True

    def draw(self, screen):
        for v in self.vessels: v.draw(screen)

    def _calculate_ground_truth_rule(self, v1, v2):
        dx, dy = v2.x - v1.x, v2.y - v1.y
        wa = math.atan2(-dy, dx);
        oh = (math.pi / 2 - v1.heading) % (2 * math.pi)
        rel = math.degrees((- (wa - oh)) % (2 * math.pi))
        if 112.5 < rel <= 247.5:
            return "Rule 13 (Overtaking)"
        elif 355 <= rel or rel <= 5:
            return "Rule 14 (Head-on)"
        elif 5 < rel <= 112.5:
            return "Rule 15 (Crossing-Stbd)"
        elif 247.5 < rel < 355:
            return "Rule 15 (Crossing-Port)"
        return "Clear"