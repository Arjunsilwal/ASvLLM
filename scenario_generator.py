from entity import Vessel, USSTucker, Francisco


def head_on_scenario(entity_manager, screen_width, screen_height):
    """
    Clears current vessels and creates two vessels placed on opposite sides
    of the screen, assigning each vessel the other's starting position as its goal.
    """
    # Optional: Clear existing vessels
    entity_manager.vessels.clear()

    # Define positions based on the screen dimensions.
    # For a head-on scenario, one vessel on the left, one on the right,
    # both centered vertically.
    left_x = screen_width * 0.2
    right_x = screen_width * 0.8
    center_y = screen_height / 2

    # Create two vessels (or BigVessels if desired)
    vessel1 = Vessel(left_x, center_y, 1000)
    vessel2 = Vessel(right_x, center_y, 1000)

    # Set goals: vessel1 moves toward vessel2's starting position, and vice versa.
    vessel1.goal = (right_x, center_y)
    vessel2.goal = (left_x, center_y)

    # Add the vessels to the entity manager
    entity_manager.vessels.append(vessel1)
    entity_manager.vessels.append(vessel2)


def cross_over_scenario(entity_manager, screen_width, screen_height):
    """
        Clears any existing vessels and creates two vessels arranged so that:
          - Vessel 1 moves from the mid-point of the lower screen to the mid-point of the top.
          - Vessel 2 moves from the mid-point of the right side to the mid-point of the left.
        """
    # Clear any existing vessels from the entity manager
    entity_manager.vessels.clear()

    # Vessel 1: from lower center to top center.
    vessel1_start_x = screen_width / 2
    vessel1_start_y = screen_height * 0.9  # near the bottom (90% down the screen)
    vessel1_goal_x = screen_width / 2
    vessel1_goal_y = screen_height * 0.1  # near the top (10% down the screen)

    # Vessel 2: from right center to left center.
    vessel2_start_x = screen_width * 0.9
    vessel2_start_y = screen_height / 2
    vessel2_goal_x = screen_width * 0.1
    vessel2_goal_y = screen_height / 2

    # Create the vessels.
    vessel1 = Vessel(vessel1_start_x, vessel1_start_y, 1000)
    vessel2 = Vessel(vessel2_start_x, vessel2_start_y, 1000)

    # Assign the respective goals
    vessel1.goal = (vessel1_goal_x, vessel1_goal_y)
    vessel2.goal = (vessel2_goal_x, vessel2_goal_y)

    # Add the vessels to the entity manager
    entity_manager.vessels.append(vessel1)
    entity_manager.vessels.append(vessel2)


def over_taking_scenario(entity_manager, screen_width, screen_height):
    """
           Clears any existing vessels and creates two vessels arranged so that:
             - Vessel 1 moves from the mid-point of the lower screen to the mid-point of the top.
             - Vessel 2 moves from the mid-point of the lower screen but with higher speed to the top of the screen.
             We can adjust the goal location of vessel 2.
           """
    # Clear any existing vessels from the entity manager
    entity_manager.vessels.clear()

    # Vessel 1: from lower center to top center.
    vessel1_start_x = screen_width / 2
    vessel1_start_y = screen_height * 0.7  # near the bottom (80% down the screen)
    vessel1_goal_x = screen_width / 2
    vessel1_goal_y = screen_height * 0.3  # near the top (20% down the screen)

    # Vessel 2: from lower center to top center.
    vessel2_start_x = screen_width / 2
    vessel2_start_y = screen_height * 0.9  # near the bottom (90% down the screen)
    vessel2_goal_x = screen_width / 2
    vessel2_goal_y = screen_height * 0.05  # near the top (10% down the screen)

    # Create the vessels.
    vessel1 = Vessel(vessel1_start_x, vessel1_start_y, 1000)
    vessel2 = Francisco(vessel2_start_x, vessel2_start_y, 1000)

    # Assign the respective goals
    vessel1.goal = (vessel1_goal_x, vessel1_goal_y)
    vessel2.goal = (vessel2_goal_x, vessel2_goal_y)

    # Add the vessels to the entity manager
    entity_manager.vessels.append(vessel1)
    entity_manager.vessels.append(vessel2)
