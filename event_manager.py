import pygame


class EventManager:
    def __init__(self, game_manager):
        self.game_manager = game_manager

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_manager.running = False
            else:
                self.handle_event(event)

    def handle_event(self, event):
        # Get a reference to the entity manager for convenience
        entity_manager = self.game_manager.entity_manager

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left-click for selection
                if entity_manager.context_menu and not entity_manager.context_menu.contains_point(event.pos):
                    entity_manager.context_menu = None
                elif entity_manager.context_menu:
                    selected_option = entity_manager.context_menu.handle_click(event.pos)
                    if selected_option:
                        entity_manager.handle_context_selection(selected_option)
                        entity_manager.context_menu = None
                else:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:  # Multi-select
                        for vessel in entity_manager.vessels:
                            if vessel.contains_point(event.pos):
                                vessel.set_selected(not vessel.selected)
                                return
                    else:  # Single-select: deselect all, then select if applicable
                        for vessel in entity_manager.vessels:
                            vessel.set_selected(False)
                        for vessel in entity_manager.vessels:
                            if vessel.contains_point(event.pos):
                                vessel.set_selected(True)
                                return

            elif event.button == 3:  # Right-click
                selected_vessels = [vessel for vessel in entity_manager.vessels if vessel.selected]
                if selected_vessels:
                    # If one or more boxes are selected, assign the goal to them
                    goal = event.pos
                    if goal not in entity_manager.goal_queue:
                        entity_manager.goal_queue.append(goal)
                    for vessel in selected_vessels:
                        vessel.goal = goal
                    entity_manager.context_menu = None
                else:
                    # If no box is selected, show the context menu
                    for vessel in entity_manager.vessels:
                        if vessel.contains_point(event.pos):
                            entity_manager.show_context_menu(event.pos, ["Delete Vessel"])
                            return
                    entity_manager.show_context_menu(event.pos,
                                                     ["Create Vessel", "Head-On Scenario",
                                                      "Cross Over Scenario", "Over Taking Scenario","Multi vessel Scenario","Multi vessel Scenario2"
                                                      ])

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:  # Press 'm' to start movement
                entity_manager.movement_active = True

