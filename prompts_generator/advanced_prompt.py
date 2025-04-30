import math


def calculate_relative_bearing(own_ship, target_ship):
    dx = target_ship.x - own_ship.x
    dy = target_ship.y - own_ship.y
    world_angle = math.atan2(-dy, dx)
    own_heading = (math.pi / 2 - own_ship.heading) % (2 * math.pi)
    rel = world_angle - own_heading
    return math.degrees((-rel) % (2 * math.pi))


def compute_tcpa_dcpa(own_ship, other_ship, pixels_per_km):
    dx = (other_ship.x - own_ship.x) / pixels_per_km
    dy = (other_ship.y - own_ship.y) / pixels_per_km
    rvx = (other_ship.desired_velocity[0] - own_ship.desired_velocity[0]) / pixels_per_km
    rvy = (other_ship.desired_velocity[1] - own_ship.desired_velocity[1]) / pixels_per_km
    rv2 = rvx ** 2 + rvy ** 2
    if rv2 == 0:
        return float('inf'), math.hypot(dx, dy)
    tcpa = - (dx * rvx + dy * rvy) / rv2
    cx = dx + rvx * tcpa
    cy = dy + rvy * tcpa
    dcpa = math.hypot(cx, cy)
    return tcpa, dcpa


def classify_situation(own_ship, other_ship, pixels_per_km,
                       head_on_threshold=15, overtaking_speed_diff=0.1):
    # heading difference
    hd = abs(((own_ship.heading - other_ship.heading) + math.pi) % (2 * math.pi) - math.pi)
    if abs(math.degrees(hd) - 180) < head_on_threshold:
        return "Head-on"

    # relative bearing
    dx = other_ship.x - own_ship.x
    dy = other_ship.y - own_ship.y
    abs_bearing = math.atan2(dy, dx)
    rel = ((abs_bearing - own_ship.heading + math.pi) % (2 * math.pi)) - math.pi
    rel_deg = math.degrees(rel)

    # relative speed
    rel_speed = (other_ship.speed - own_ship.speed) / pixels_per_km * 3600
    # overtaking
    if rel_speed > overtaking_speed_diff and abs(rel_deg) < 45:
        return "Overtaking"

    # crossing
    if -90 <= rel_deg <= 90:
        return "Crossing"

    # default overtaking if faster
    if rel_speed > overtaking_speed_diff:
        return "Overtaking"
    return "Crossing"


def generate_vessel_prompt(vessels, pixels_per_km=1):
    prompt = (
        "You are an expert maritime navigation AI. Provide COLREGs-compliant maneuvers."
        " Include the following data for each vessel encounter."
        " Respond ONLY with a JSON array of {id, situation, role, action}. No extra text.\n"
        "Detailed Data Provided:\n"
        "- Position (px), heading (°), speed (km/h)\n"
        "- Relative bearing (°), distance (km), TCPA (s), DCPA (km) for each pair\n"
        "- Computed situation: Head-on, Crossing, or Overtaking based on relative heading & speed.\n"
        "Use this to decide the correct maneuver.\n\n"
        "Vessels Data:\n"
    )
    for v in vessels:
        speed_kmh = (v.speed / pixels_per_km * 3600) if pixels_per_km else 0
        prompt += f"- id: {id(v)}, pos: ({v.x:.1f},{v.y:.1f}), heading: {math.degrees(v.heading):.1f}°, speed: {speed_kmh:.1f} km/h\n"
        prompt += "  Other vessels:\n"
        for o in vessels:
            if o is v:
                continue
            dist_km = math.hypot(o.x - v.x, o.y - v.y) / pixels_per_km
            rb = calculate_relative_bearing(v, o)
            tcpa, dcpa = compute_tcpa_dcpa(v, o, pixels_per_km)
            situation = classify_situation(v, o, pixels_per_km)
            prompt += (
                f"    - id: {id(o)}, situation: {situation}, dist: {dist_km:.3f} km, relBearing: {rb:.1f}°, "
                f"TCPA: {tcpa:.1f}s, DCPA: {dcpa:.3f} km\n"
            )
    return prompt
