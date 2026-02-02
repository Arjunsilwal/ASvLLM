import math

def calculate_relative_bearing(own_ship, target_ship):
    dx = target_ship.x - own_ship.x; dy = target_ship.y - own_ship.y
    world_angle = math.atan2(-dy, dx)
    own_heading = (math.pi / 2 - own_ship.heading) % (2 * math.pi)
    rel = world_angle - own_heading
    return math.degrees((-rel) % (2 * math.pi))

def generate_vessel_prompt(vessels_to_describe, all_context_vessels, pixels_per_km=1, previous_vessel_data_list=None, previous_responses=None):
    prompt = ("""
        "Ship navigation according to COLREGs.\n"
        "Determine the situation, role, and action. Provide a short technical explanation.\n"
        "Format: JSON array of objects {id, situation, role, action, explanation}.\n"
        "Explanation style: Technical phrase (e.g., 'Rule 15 - Vessel on starboard').\n"

    Rules:
      1. Head-on: reciprocal courses -> Alter course to starboard.
      2. Crossing: vessel with other on its starboard side -> Give-way.
      3. Overtaking: faster vessel from behind -> Give-way.

    Vessels Data:
    """
    )
    for v in vessels_to_describe:
        speed_kmh = (v.speed / pixels_per_km * 3600) if pixels_per_km else 0
        prompt += f"- id: {id(v)}, heading: {math.degrees(v.heading):.1f}°, speed: {speed_kmh:.1f} km/h\n"
        prompt += "  Other vessels:\n"
        for o in all_context_vessels:
            if o is v: continue
            dist = math.hypot(o.x - v.x, o.y - v.y) / pixels_per_km
            rb = calculate_relative_bearing(v, o)
            prompt += f"    - id: {id(o)}, speed: {(o.speed / pixels_per_km * 3600):.1f} km/h, dist: {dist:.3f} km, relBrg: {rb:.1f}°\n"
    return prompt