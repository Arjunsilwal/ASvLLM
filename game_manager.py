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
        self.current_experiment_id = 0

    def load_simulation_from_ui(self):
        mode = self.ui_manager.get_value("mode")
        llm = self.ui_manager.get_value("llm")
        prompt = self.ui_manager.get_value("prompt")
        scenario = self.ui_manager.get_value("scenario")
        print(f"UI Trigger: Loading {scenario} | {mode} | {llm}")
        self.load_simulation_scripted(mode, llm, prompt, scenario, experiment_id=0)

    def load_simulation_scripted(self, mode, llm, prompt, scenario, experiment_id=0):
        self.current_mode = mode
        self.current_llm = llm
        self.current_prompt_type = prompt
        self.current_experiment_id = experiment_id

        # Map to the 3 distinct intelligence levels
        mode_to_file = {
            "natural": "entity_manager_natural_language",
            "prompt_history": "entity_manager_prompt_history",
            "standard": "entity_manager_standard"
        }

        target_module_name = mode_to_file.get(mode, "entity_manager_standard")

        try:
            module = importlib.import_module(target_module_name)
            importlib.reload(module)
            self.entity_manager = getattr(module, "EntityManager")(self, llm_provider=llm)
            self.entity_manager.load_scenario(scenario)
            self.paused = False
        except Exception as e:
            print(f"Failed to load {target_module_name}: {e}")

    async def run_async(self):
        clock = pygame.time.Clock()
        while self.running:
            self.event_manager.handle_events(pygame.event.get())
            dt = min(clock.tick(60) / 1000.0, 1 / 30)
            if not self.paused and self.entity_manager:
                await self.entity_manager.update_vessels(dt)
            self.render()
            await asyncio.sleep(0)
        pygame.quit()

    def render(self):
        self.graphics_manager.clear(WHITE)
        if self.entity_manager:
            self.entity_manager.draw(self.graphics_manager.screen)
        self.ui_manager.draw(self.graphics_manager.screen)
        pygame.display.flip()