import math

def calculate_relative_bearing(own_ship, target_ship):
    dx = target_ship.x - own_ship.x
    dy = target_ship.y - own_ship.y
    world_angle_rad = math.atan2(-dy, dx)
    own_heading_rad = (math.pi / 2 - own_ship.heading) % (2 * math.pi)
    relative_angle_rad = world_angle_rad - own_heading_rad
    relative_bearing_rad = (-relative_angle_rad) % (2 * math.pi)
    return math.degrees(relative_bearing_rad)

def generate_vessel_prompt(vessels_to_describe, all_context_vessels, pixels_per_km=1, previous_vessel_data_list=None, previous_responses=None):
    prompt = ("""
        "Ship navigation according to COLREGs.\n"
        "For each vessel listed below, determine the situation, role, action, and a 1-word explanation.\n"
        "Respond ONLY with a JSON array of objects {id, situation, role, action, explanation}.\n"
        "Explanation style: Brief rule code (e.g., 'R15').\n"
        "Vessels Data:"
        """
    )

    for v in vessels_to_describe:
        speed_kmh = (v.speed / pixels_per_km * 3600) if pixels_per_km > 0 else 0
        prompt += f"\n- id: {id(v)}, pos: ({v.x:.1f}, {v.y:.1f}), heading: {math.degrees(v.heading):.1f}°, speed: {speed_kmh:.1f} km/h"
        prompt += "\n  Other vessels:"
        for o in all_context_vessels:
            if o is v: continue
            dist_km = math.hypot(o.x - v.x, o.y - v.y) / pixels_per_km
            rb = calculate_relative_bearing(v, o)
            prompt += f"\n    - id: {id(o)}, pos: ({o.x:.1f},{o.y:.1f}), dist: {dist_km:.3f} km, relBrg: {rb:.1f}°"
    return prompt