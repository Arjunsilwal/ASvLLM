import time
import math
import json
# --- Imports ---
from entity import Vessel, ContextMenu, USSTucker
from scenario_generator import head_on_scenario, cross_over_scenario, over_taking_scenario
from useLLm import get_llm_decision
from prompts_generator.prompt_generator import generate_multi_vessel_prompt
from response_parser import Maneuver, parse_llm_response_for_all


class EntityManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.vessels = []
        self.context_menu = None
        self.movement_active = False
        self.goal_queue = []
        self.llm_cooldown = {}
        self.llm_cooldown_duration = 0.0
        self.llm_trigger_distance_km = 0.30
        self.pixels_per_km = 1000.0

        self.llm_call_count = 0
        self.last_llm_call_time = 0.0

    def draw(self, screen):
        for vessel in self.vessels:
            vessel.draw(screen)
        if self.context_menu:
            self.context_menu.draw(screen)

    def show_context_menu(self, pos, options):
        self.context_menu = ContextMenu(pos[0], pos[1], options)

    def handle_context_selection(self, selected_option):
        screen_width = self.game_manager.graphics_manager.width
        screen_height = self.game_manager.graphics_manager.height
        center_x = self.context_menu.x + self.context_menu.width // 2
        center_y = self.context_menu.y + self.context_menu.height // 2
        if selected_option == "Create Vessel":
            # Create a box at the center of the context menu
            new_vessel = Vessel(center_x, center_y, 1000)
            self.vessels.append(new_vessel)
        elif selected_option == "Create USS Tucker":
            new_vessel = USSTucker(center_x, center_y, 1000)
            self.vessels.append(new_vessel)
        elif selected_option == "Delete Vessel":
            # Delete the first box that contains the context menu's position
            for vessel in self.vessels:
                if vessel.contains_point((self.context_menu.x, self.context_menu.y)):
                    self.vessels.remove(vessel)
                    break
        elif selected_option == "Create Head-On Scenario":
            head_on_scenario(self, screen_width, screen_height)

        elif selected_option == "Create Cross Over Scenario":
            cross_over_scenario(self, screen_width, screen_height)

        elif selected_option == "Create Over Taking Scenario":
            over_taking_scenario(self, screen_width, screen_height)

    def update_vessels(self, dt):
        if dt <= 0:
            return

        now = time.time()

        # 1) Recompute VO desired velocities
        for v in self.vessels:
            v.calculate_desired_velocity()

        # 2) Figure out which vessels still need an LLM decision
        to_query = []
        for v in self.vessels:
            neigh = [o for o in self.vessels
                     if o is not v
                     and math.hypot(v.x - o.x, v.y - o.y) / self.pixels_per_km < self.llm_trigger_distance_km]

            if not neigh:
                # no neighbors ⇒ clear maneuver & resume goal
                v.current_maneuver = None
                v.in_maneuver = False
                if self.movement_active and v.goal:
                    v.turn_towards_goal(dt)
                continue

            # convergence check
            ox, oy = v.desired_velocity
            converging = any(
                (o.x - v.x) * (o.desired_velocity[0] - ox) +
                (o.y - v.y) * (o.desired_velocity[1] - oy) < 0
                for o in neigh
            )
            if not converging:
                # diverging ⇒ clear maneuver & resume goal
                v.current_maneuver = None
                v.in_maneuver = False
                if self.movement_active and v.goal:
                    v.turn_towards_goal(dt)
                continue

            last = self.llm_cooldown.get(id(v), 0.0)
            if now - last >= self.llm_cooldown_duration:
                to_query.append(v)

        # 3) Fire one LLM prompt for all converging vessels
        if to_query:
            for v in to_query:
                self.llm_cooldown[id(v)] = now
                if not hasattr(v, "_first_llm"):
                    v._first_llm = now
                    print(f"Vessel {id(v)} first LLM @ {time.ctime(now)}")

            prompt = generate_multi_vessel_prompt(self.vessels, self.pixels_per_km)
            print("\nPrompt →\n", prompt)
            raw = get_llm_decision(prompt)
            self.llm_call_count += 1
            if raw:
                parsed = parse_llm_response_for_all(raw)
                if parsed:
                    print("Parsed:", json.dumps(parsed, indent=2))
                    for e in parsed:
                        # find vessel
                        for v in self.vessels:
                            if id(v) == e["id"]:
                                # determine maneuver
                                m = e["maneuver"]
                                # overtaking override
                                if e["situation"].lower() == "overtaking" and e["role"].lower() == "give-way":
                                    m = Maneuver.ALTER_COURSE_STARBOARD

                                # store it for continuous application
                                v.current_maneuver = m
                                # mark that we’re in it
                                v.in_maneuver = (m != Maneuver.MAINTAIN_COURSE_SPEED)
                                print(f"→ Vessel {e['id']} current_maneuver = {m.name}")
                                break
        print(self.llm_call_count)
        # 3b) **Continuously apply** any in-progress maneuver
        for v in self.vessels:
            if getattr(v, "current_maneuver", None) not in (None, Maneuver.MAINTAIN_COURSE_SPEED):
                v.apply_maneuver(v.current_maneuver, dt)
                v.calculate_desired_velocity()

        # 4) Finally, update positions & heading only if movement_active
        any_move = False
        if self.movement_active:
            for v in self.vessels:
                if not v.in_maneuver and v.goal:
                    v.turn_towards_goal(dt)
                v.update_position(dt)
                if v.goal or v.speed > 0.1:
                    any_move = True
        else:
            for v in self.vessels:
                v.speed = 0

        self.movement_active = any_move


