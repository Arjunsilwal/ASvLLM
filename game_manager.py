import pygame
from entity_manager import EntityManager
from graphics_manager import GraphicsManager
from event_manager import EventManager
from entity import WHITE  # Using WHITE defined in entity.py


class GameManager:
    def __init__(self, width, height):
        self.running = True
        self.entity_manager = EntityManager(self)
        self.graphics_manager = GraphicsManager(width, height, "ASV")
        self.event_manager = EventManager(self)

    def run(self):
        clock = pygame.time.Clock()
        while self.running:
            self.event_manager.handle_events()
            dt = clock.tick(60) / 1000.0
            self.update(dt)
            self.render()
            clock.tick(60)
        self.entity_manager.export_log("experiments/detailed/detailed_prompt_overtaking_experiment_1.csv")
        pygame.quit()

    def update(self, dt):
        self.entity_manager.update_vessels(dt)

    def render(self):
        self.graphics_manager.clear(WHITE)
        self.entity_manager.draw(self.graphics_manager.screen)
        self.graphics_manager.update_display()
