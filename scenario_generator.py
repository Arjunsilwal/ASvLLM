import math
from entity import Vessel, Francisco

# Define a list of colors to cycle through for the vessels
VESSEL_COLORS = [
    (255, 0, 0),  # Red
    (0, 0, 255),  # Blue
    (0, 255, 0),  # Green
    (255, 165, 0),  # Orange
    (128, 0, 128),  # Purple
]


# Coordinate Convention:
# 0 is North (Up), pi/2 is East (Right), pi is South (Down), 3pi/2 is West (Left)

def head_on_scenario(manager, sw, sh):
    manager.vessels.clear()
    manager._sim_time = 0.0

    v1 = Vessel(100, sh // 2, manager.pixels_per_km, color=VESSEL_COLORS[0])
    v1.heading = math.pi / 2
    v1.speed = v1.max_speed
    v1.goal = [sw - 100, sh // 2]

    v2 = Vessel(sw - 100, sh // 2, manager.pixels_per_km, color=VESSEL_COLORS[1])
    v2.heading = 3 * math.pi / 2
    v2.speed = v2.max_speed
    v2.goal = [100, sh // 2]

    manager.vessels.extend([v1, v2])


def cross_over_scenario(manager, sw, sh):
    manager.vessels.clear()
    v1 = Vessel(sw // 2, sh - 100, manager.pixels_per_km, color=VESSEL_COLORS[0])
    v1.heading = 0
    v1.speed = v1.max_speed
    v1.goal = [sw // 2, 100]

    v2 = Vessel(100, sh // 2, manager.pixels_per_km, color=VESSEL_COLORS[1])
    v2.heading = math.pi / 2
    v2.speed = v2.max_speed
    v2.goal = [sw - 100, sh // 2]

    manager.vessels.extend([v1, v2])


def over_taking_scenario(manager, sw, sh):
    """
    Arranges two vessels so that:
      - Vessel 1 (Stand-on) moves slowly from lower screen to top.
      - Vessel 2 (Francisco/Give-way) moves faster from below Vessel 1 to overtake it.
    """
    manager.vessels.clear()

    # Vessel 1 (Slower - Stand-on): from lower center to top center
    v1_start_x = sw / 2
    v1_start_y = sh * 0.7
    v1_goal_x = sw / 2
    v1_goal_y = sh * 0.1  # Target near top

    # Vessel 2 (Faster - Overtaking/Give-way): starts further back
    v2_start_x = sw / 2
    v2_start_y = sh * 0.9
    v2_goal_x = sw / 2
    v2_goal_y = sh * (-10.5) # Extremely far goal to maintain high speed overtaking

    # Create the vessels
    v1 = Vessel(v1_start_x, v1_start_y, manager.pixels_per_km, color=VESSEL_COLORS[1]) # Blue
    v2 = Francisco(v2_start_x, v2_start_y, manager.pixels_per_km) # Red (Francisco is faster)

    # Set Initial states for Overtaking
    v1.heading = 0.0 # North
    v1.speed = v1.max_speed * 0.5 # Moving at half speed
    v1.goal = [v1_goal_x, v1_goal_y]

    v2.heading = 0.0 # North
    v2.speed = v2.max_speed # Moving at full speed
    v2.goal = [v2_goal_x, v2_goal_y]

    manager.add_vessel(v1)
    manager.add_vessel(v2)

def multi_vessel_scenario(manager, sw, sh):
    """3-vessel convergence meeting in center."""
    manager.vessels.clear()
    v1 = Vessel(150, 150, manager.pixels_per_km, color=VESSEL_COLORS[0])
    v1.heading = math.pi * 0.75
    v1.speed = v1.max_speed
    v1.goal = [sw - 150, sh - 150]

    v2 = Vessel(sw - 150, 150, manager.pixels_per_km, color=VESSEL_COLORS[1])
    v2.heading = math.pi * 1.25
    v2.speed = v2.max_speed
    v2.goal = [150, sh - 150]

    v3 = Vessel(sw // 2, sh - 150, manager.pixels_per_km, color=VESSEL_COLORS[2])
    v3.heading = 0
    v3.speed = v3.max_speed
    v3.goal = [sw // 2, 150]

    manager.vessels.extend([v1, v2, v3])


def multi_vessel_scenario_2(manager, sw, sh):
    """
    Another 3-vessel scenario: One Eastbound, two converging from North-East and South-East.
    """
    manager.vessels.clear()
    manager._sim_time = 0.0

    # Vessel 1: Red (West to East)
    v1 = Vessel(100, sh // 2, manager.pixels_per_km, color=VESSEL_COLORS[0])
    v1.heading = math.pi / 2
    v1.speed = v1.max_speed
    v1.goal = [sw - 100, sh // 2]

    # Vessel 2: Blue (North-East to South-West)
    v2 = Vessel(sw - 200, 150, manager.pixels_per_km, color=VESSEL_COLORS[1])
    v2.heading = math.pi * 1.25
    v2.speed = v2.max_speed
    v2.goal = [200, sh - 150]

    # Vessel 3: Green (South-East to North-West)
    v3 = Vessel(sw - 200, sh - 150, manager.pixels_per_km, color=VESSEL_COLORS[2])
    v3.heading = math.pi * 1.75
    v3.speed = v3.max_speed
    v3.goal = [200, 150]

    manager.vessels.extend([v1, v2, v3])


def multi_vessel_scenario_3(manager, sw, sh):
    """
    4-vessel complex scenario: The 'Cross' convergence.
    """
    manager.vessels.clear()
    manager._sim_time = 0.0

    # Vessel 1: Red (North to South)
    v1 = Vessel(sw // 2, 100, manager.pixels_per_km, color=VESSEL_COLORS[0])
    v1.heading = math.pi  # South
    v1.speed = v1.max_speed
    v1.goal = [sw // 2, sh - 100]

    # Vessel 2: Blue (South to North)
    v2 = Vessel(sw // 2, sh - 100, manager.pixels_per_km, color=VESSEL_COLORS[1])
    v2.heading = 0  # North
    v2.speed = v2.max_speed
    v2.goal = [sw // 2, 100]

    # Vessel 3: Green (West to East)
    v3 = Vessel(100, sh // 2, manager.pixels_per_km, color=VESSEL_COLORS[2])
    v3.heading = math.pi / 2  # East
    v3.speed = v3.max_speed
    v3.goal = [sw - 100, sh // 2]

    # Vessel 4: Orange (East to West)
    v4 = Vessel(sw - 100, sh // 2, manager.pixels_per_km, color=VESSEL_COLORS[3])
    v4.heading = 3 * math.pi / 2  # West
    v4.speed = v4.max_speed
    v4.goal = [100, sh // 2]

    manager.vessels.extend([v1, v2, v3, v4])


def traffic_separation_scenario(manager, sw, sh):
    """
    TSS with horizontal lanes and vertical AI crossing.
    """
    manager.vessels.clear()
    top_lane_y = sh * 0.35
    bottom_lane_y = sh * 0.60
    spacing = sw / 2.5

    # Eastbound Lane (Green - Rightward)
    for i in range(5):
        start_x = 50 - (i * spacing)
        v = Vessel(start_x, bottom_lane_y, 1000, color=VESSEL_COLORS[2])
        v.heading = math.pi / 2
        v.tss_target_heading = math.pi / 2 # LOCK HEADING
        v.speed = v.max_speed; v.goal = [sw + 2000, bottom_lane_y]
        manager.add_vessel(v)

    # Westbound Lane (Orange - Leftward)
    for i in range(5):
        start_x = (sw - 50) + (i * spacing)
        v = Vessel(start_x, top_lane_y, 1000, color=VESSEL_COLORS[3])
        v.heading = 3 * math.pi / 2
        v.tss_target_heading = 3 * math.pi / 2 # LOCK HEADING
        v.speed = v.max_speed; v.goal = [-2000, top_lane_y]
        manager.add_vessel(v)

    # Crossing Vessel (Red - AI Controlled)
    red = Francisco(sw / 2, sh * 0.9, 1000)
    red.heading = 0.0
    red.tss_target_heading = 0.0
    red.goal = [sw / 2, sh * 0.1]
    manager.add_vessel(red)