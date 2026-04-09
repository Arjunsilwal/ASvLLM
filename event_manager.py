import pygame

class EventManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager

    def handle_events(self, events):
        """Processes Pygame events and communicates with UI and Game Manager."""
        for event in events:
            if event.type == pygame.QUIT:
                self.game_manager.running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.game_manager.running = False

            # Route event to UI and check for returned actions
            actions = self.game_manager.ui_manager.handle_event(event)

            if actions.get('load'):
                self.game_manager.load_simulation_from_ui()

            if actions.get('pause'):
                self.game_manager.paused = not self.game_manager.paused