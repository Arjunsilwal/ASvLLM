import math

def calculate_relative_bearing(own_ship, target_ship):
    dx = target_ship.x - own_ship.x; dy = target_ship.y - own_ship.y
    world_angle = math.atan2(-dy, dx)
    own_heading = (math.pi / 2 - own_ship.heading) % (2 * math.pi)
    rel = world_angle - own_heading
    return math.degrees((-rel) % (2 * math.pi))

def compute_tcpa_dcpa(own_ship, other_ship, pixels_per_km):
    dx = (other_ship.x - own_ship.x) / pixels_per_km
    dy = (other_ship.y - own_ship.y) / pixels_per_km
    rvx = (other_ship.desired_velocity[0] - own_ship.desired_velocity[0]) / pixels_per_km
    rvy = (other_ship.desired_velocity[1] - own_ship.desired_velocity[1]) / pixels_per_km
    rv2 = rvx**2 + rvy**2
    if rv2 == 0: return float('inf'), math.hypot(dx, dy)
    tcpa = - (dx * rvx + dy * rvy) / rv2
    dcpa = math.hypot(dx + rvx * max(0, tcpa), dy + rvy * max(0, tcpa))
    return tcpa, dcpa

def generate_vessel_prompt(vessels_to_describe, all_context_vessels, pixels_per_km=1, previous_vessel_data_list=None, previous_responses=None):
    prompt = ("""
        "Expert Ship navigation according to COLREGs.\n"
        "Analyze the data and provide a professional navigational justification.\n"
        "Format: JSON array of objects {id, situation, role, action, explanation}.\n"
        "Explanation style: Professional justification citing specific COLREGs Rules.\n"

        "Rules Summary:\n"
        "1) Head-on (Rule 14): reciprocal courses -> Alter course to starboard.\n"
        "2) Crossing (Rule 15): Target on starboard 0°-112.5° -> Give-way.\n"
        "3) Overtaking (Rule 13): Approaching from >112.5° relative -> Give-way.\n"

        "Vessels Data:\n"
         """
    )
    for v in vessels_to_describe:
        speed_kmh = (v.speed / pixels_per_km * 3600)
        prompt += f"- id: {id(v)}, heading: {math.degrees(v.heading):.1f}°, speed: {speed_kmh:.1f} km/h\n"
        prompt += "  Other vessels:\n"
        for o in all_context_vessels:
            if o is v: continue
            dist_km = math.hypot(o.x - v.x, o.y - v.y) / pixels_per_km
            rb = calculate_relative_bearing(v, o)
            tcpa, dcpa = compute_tcpa_dcpa(v, o, pixels_per_km)
            prompt += f"    - id: {id(o)}, dist: {dist_km:.3f} km, relBrg: {rb:.1f}°, TCPA: {tcpa:.1f}s, DCPA: {dcpa:.3f} km\n"
    return prompt