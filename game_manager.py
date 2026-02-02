import pygame
import os
import asyncio
import importlib
from graphics_manager import GraphicsManager
from event_manager import EventManager
from entity import WHITE
from ui_manager import UIManager


class GameManager:
    def __init__(self, width, height):
        self.running = True
        self.paused = False
        self.graphics_manager = GraphicsManager(width, height, "ASV Simulation")
        self.event_manager = EventManager(self)

        self.ui_manager = UIManager(width)
        self.entity_manager = None
        self.current_mode = None
        self.current_llm = None
        self.current_prompt_type = None

    def load_simulation_scripted(self, mode, llm, prompt, scenario):
        """
        Allows a python script to load a simulation directly
        without using the UI dropdowns.
        """
        self.current_mode = mode
        self.current_llm = llm
        self.current_prompt_type = prompt

        mode_to_file = {
            "natural": "entity_manager_natural_language",
            "prompt_history": "entity_manager_prompt_history",
            "standard": "entity_manager_standard",
            "tss": "entity_manager_tss"
        }

        target_module_name = mode_to_file.get(mode, "entity_manager_standard")
        import importlib
        module = importlib.import_module(target_module_name)
        importlib.reload(module)

        self.entity_manager = getattr(module, "EntityManager")(self, llm_provider=llm)
        self.entity_manager.load_scenario(scenario)
        self.paused = False
        print(f">>> BATCH RUN: Mode={mode}, Scenario={scenario}")

    def load_simulation(self):
        """
        Dynamically loads the correct EntityManager based on UI selections.
        This allows switching between 'Natural', 'P+H', and 'Hybrid' at runtime.
        """
        # 1. Get configuration from UI
        self.current_mode = self.ui_manager.get_value("mode")
        self.current_llm = self.ui_manager.get_value("llm")
        self.current_prompt_type = self.ui_manager.get_value("prompt")
        selected_scenario = self.ui_manager.get_value("scenario")

        print(f"\n--- Loading Simulation ---")
        print(f"  Mode: {self.current_mode}")
        print(f"  LLM: {self.current_llm}")
        print(f"  Scenario: {selected_scenario}")

        # 2. Map UI mode values to specific file names
        mode_to_file = {
            "natural": "entity_manager_natural_language",
            "prompt_history": "entity_manager_prompt_history",
            "hybrid": "entity_manager_hybrid",
            "tss": "entity_manager_tss",
            "rag": "entity_manager2",
            "standard": "entity_manager_standard"
        }

        target_module_name = mode_to_file.get(self.current_mode, "entity_manager_standard")

        try:
            # 3. Dynamic Import
            # This replaces the need for a single massive entity_manager_standard.py
            module = importlib.import_module(target_module_name)
            # Ensure the module is reloaded in case you made code changes
            importlib.reload(module)

            EntityManagerClass = getattr(module, "EntityManager")

            # 4. Initialize the manager with the selected LLM
            self.entity_manager = EntityManagerClass(
                self,
                llm_provider=self.current_llm
            )

            # 5. Load the Scenario (Head-on, Crossing, etc.)
            # Most of our managers use 'load_scenario', some use 'handle_context_selection'
            if hasattr(self.entity_manager, 'load_scenario'):
                self.entity_manager.load_scenario(selected_scenario)
            elif hasattr(self.entity_manager, 'handle_context_selection'):
                self.entity_manager.handle_context_selection(selected_scenario)

            # 6. Reset UI State
            self.paused = False
            if 'pause' in self.ui_manager.action_buttons:
                self.ui_manager.action_buttons['pause'].value = "running"
                self.ui_manager.action_buttons['pause'].update_text("PAUSE")

            print(f"Successfully loaded {target_module_name} with {self.current_llm}")

        except Exception as e:
            print(f"ERROR: Failed to load simulation mode '{self.current_mode}': {e}")
            import traceback
            traceback.print_exc()
            self.entity_manager = None

    async def run_async(self):
        """The main asynchronous game loop."""
        clock = pygame.time.Clock()
        while self.running:
            events = pygame.event.get()

            # --- Handle Events ---
            self.event_manager.handle_events(events)
            ui_actions = self.ui_manager.handle_events(events)

            if ui_actions['load']:
                self.load_simulation()

            if ui_actions['pause']:
                self.paused = not self.paused

            # --- Update Simulation ---
            dt = clock.tick(60) / 1000.0
            dt = min(dt, 1 / 30)  # Physics safety cap

            if not self.paused and self.entity_manager:
                # We await because LLM calls inside update_vessels are async
                await self.entity_manager.update_vessels(dt)

            # --- Render ---
            self.render()
            await asyncio.sleep(0)  # Yield control to prevent UI freezing

        pygame.quit()

    def render(self):
        """Draws the simulation layer and the UI layer."""
        self.graphics_manager.clear(WHITE)

        if self.entity_manager:
            self.entity_manager.draw(self.graphics_manager.screen)

            # Screenshot logic for logs
            if getattr(self.entity_manager, 'take_screenshot_on_next_render', False):
                filename = f"llm_{self.entity_manager.llm_call_count}_time_{self.entity_manager._sim_time:.1f}s.png"
                screenshot_dir = getattr(self.entity_manager, 'screenshot_dir', 'screenshots_natural')
                if not os.path.exists(screenshot_dir):
                    os.makedirs(screenshot_dir)
                filepath = os.path.join(screenshot_dir, filename)
                pygame.image.save(self.graphics_manager.screen, filepath)
                self.entity_manager.take_screenshot_on_next_render = False

        self.ui_manager.draw(self.graphics_manager.screen)
        self.graphics_manager.update_display()