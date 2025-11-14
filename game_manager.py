import pygame
import os
import asyncio
from graphics_manager import GraphicsManager
from event_manager import EventManager
from entity import WHITE

class GameManager:
    def __init__(self, width, height, mode='rag'): # <-- Add 'mode' argument
        self.running = True
        self.graphics_manager = GraphicsManager(width, height, "ASV")
        self.event_manager = EventManager(self)
        self.mode = mode

        # --- DYNAMICALLY IMPORT AND CREATE THE CORRECT ENTITY MANAGER ---
        if self.mode == 'natural':
            from entity_manager_natural_language import EntityManager
            self.entity_manager = EntityManager(self)
            print("Vision with natural language EntityManager loaded.")
        elif self.mode == "hybrid":
            from entity_manager_hybrid import EntityManager
            self.entity_manager = EntityManager(self)
            print("Hybrid EntityManager loaded.")
        else: # Default to the original RAG manager
            from entity_manager2 import EntityManager # Assuming this is your final RAG manager
            self.entity_manager = EntityManager(self)
            print("RAG EntityManager loaded.")
        # --- END OF DYNAMIC IMPORT ---

    # --- The ORIGINAL, SYNCHRONOUS game loop ---
    def run_sync(self):
        clock = pygame.time.Clock()
        while self.running:
            self.event_manager.handle_events()
            dt = clock.tick(60) / 1000.0
            self.update_sync(dt) # Call the sync update
            self.render()
        self.entity_manager.export_log("...path_to_your_rag_log.csv")
        pygame.quit()

    def update_sync(self, dt):
        self.entity_manager.update_vessels(dt) # This is a normal function call

    # --- The NEW, ASYNCHRONOUS game loop for the vision experiment ---
    async def run_async(self):
        clock = pygame.time.Clock()
        while self.running:
            self.event_manager.handle_events()
            dt = clock.tick(60) / 1000.0

            # --- ADD THIS LINE TO FIX THE JUMP ---
            # Cap dt to a maximum of 1/30th of a second (a 30 FPS frame).
            # This prevents huge time steps after the API call freeze.
            dt = min(dt, 1/30)
            # --- END OF FIX ---

            await self.update_async(dt) # Call the async update
            self.render()
            await asyncio.sleep(0) # Yield control
        # Note: You might need a different log path for your vision experiment
        # self.entity_manager.export_log("...path_to_your_vision_log.csv")
        pygame.quit()

    async def update_async(self, dt):
        await self.entity_manager.update_vessels(dt) # This is an awaited coroutine call

    def render(self):
        self.graphics_manager.clear(WHITE)
        self.entity_manager.draw(self.graphics_manager.screen)
        if self.entity_manager.take_screenshot_on_next_render:
            # ... (Your screenshot logic remains here and works for both modes)
            filename = (f"llm_call_{self.entity_manager.llm_call_count}_time_{self.entity_manager._sim_time:.1f}s.png")
            screenshot_dir = self.entity_manager.screenshot_dir
            if not os.path.exists(screenshot_dir): os.makedirs(screenshot_dir)
            filepath = os.path.join(screenshot_dir, filename)
            pygame.image.save(self.graphics_manager.screen, filepath)
            print(f"--- Screenshot saved: {filepath} ---")
            self.entity_manager.take_screenshot_on_next_render = False
        self.graphics_manager.update_display()