import math
import json


# calculate_relative_bearing function is unchanged...
def calculate_relative_bearing(own_ship, target_ship):
    """Calculates bearing of target relative to own ship's heading (0=ahead, 90=starboard/CW)."""
    dx = target_ship.x - own_ship.x
    dy = target_ship.y - own_ship.y
    world_angle_rad = math.atan2(-dy, dx)
    own_heading_rad = (math.pi / 2 - own_ship.heading) % (2 * math.pi)
    relative_angle_rad = world_angle_rad - own_heading_rad
    relative_bearing_rad = (-relative_angle_rad) % (2 * math.pi)
    return math.degrees(relative_bearing_rad)


# calculate_cpa_details is unchanged...
def calculate_cpa_details(v1, v2, pixels_per_km):
    p_rel_x = v1.x - v2.x
    p_rel_y = v1.y - v2.y
    v1_vx, v1_vy = v1.speed * math.sin(v1.heading), -v1.speed * math.cos(v1.heading)
    v2_vx, v2_vy = v2.speed * math.sin(v2.heading), -v2.speed * math.cos(v2.heading)
    v_rel_x = v1_vx - v2_vx
    v_rel_y = v1_vy - v2_vy
    v_rel_mag_sq = v_rel_x ** 2 + v_rel_y ** 2
    if v_rel_mag_sq == 0: return None, None
    dot_product = (p_rel_x * v_rel_x) + (p_rel_y * v_rel_y)
    tcpa = -dot_product / v_rel_mag_sq
    if tcpa < 0: return None, None
    future_x1 = v1.x + v1_vx * tcpa
    future_y1 = v1.y + v1_vy * tcpa
    future_x2 = v2.x + v2_vx * tcpa
    future_y2 = v2.y + v2_vy * tcpa
    dist_sq = (future_x1 - future_x2) ** 2 + (future_y1 - future_y2) ** 2
    dcpa_km = math.sqrt(dist_sq) / pixels_per_km if pixels_per_km > 0 else 0
    return tcpa, dcpa_km


# --- UPDATED FUNCTION SIGNATURE and PROMPT STRING ---
def generate_tss_crossing_prompt(vessels_to_describe, all_context_vessels, pixels_per_km=1,
                                 previous_vessel_data_list=None, previous_responses=None):
    """
    Generates a prompt for TSS crossing, including structured historical context.
    """
    prompt = ("""
"You are a meticulous ship navigation AI following COLREGs Rule 10 (TSS) and Rules 13-17.
Analyze the image, current data, and recent history for the **single crossing vessel** below.

**OVERRIDING OBJECTIVE (Rule 10(c)):** Your primary goal is to maintain a heading as nearly as practicable at right angles (perpendicular, Target Heading: 0°/North or 180°/South) to the traffic flow. **Deviations from this heading are temporary and must be minimized.**

"""
              )

    # --- NEW, ROBUST HISTORY SECTION ---
    if previous_vessel_data_list and previous_responses and len(previous_vessel_data_list) == len(previous_responses):
        prompt += "**Recent History (Most recent first):**\n"
        for i in range(len(previous_vessel_data_list) - 1, -1, -1):
            history_step = len(previous_vessel_data_list) - i
            prompt += f"--- History Step T-{history_step} ---\n"

            prompt += f"Vessel States (T-{history_step}):\n"
            for vessel_state in previous_vessel_data_list[i]:
                prompt += f"  - id: {vessel_state['id']}, pos: {vessel_state['pos']}, heading: {vessel_state['heading_deg']}°, speed: {vessel_state['speed_kmh']} km/h\n"

            prompt += f"Decision Made (T-{history_step}):\n"
            for decision in previous_responses[i]:
                prompt += f"  - id: {decision.get('id', 'N/A')}, situation: {decision.get('situation', 'N/A')}, role: {decision.get('role', 'N/A')}, action: {decision.get('action', 'N/A')}\n"
            prompt += "\n"
        prompt += "---\n\n"
    # --- END HISTORY SECTION ---

    prompt += "**Current Situation Analysis & Action Required:**\n"
    # Append the rest of your existing detailed TSS instructions
    prompt += """
**Action Strategy (Prioritizing Perpendicular Track):**
Your task is to choose the *single best action* from the list below.
1.  **Assess Risk:** Look at the 'Other vessels' data. Pay close attention to `dist_km` and `TCPA` (Time to Closest Point of Approach).
2.  **IF PATH IS CLEAR (No conflict):**
    - **Check Speed:** Is the vessel already at its max speed (approx 107 km/h for Francisco)?
        - **IF YES:** Action: 'Maintain course and speed'
        - **IF NO:** Action: 'Accelerate' (This is the command to reach max speed while on the perpendicular track).
3.  **IF CONFLICT EXISTS (RISK OF COLLISION):**
    - **First, analyze speed:** Can the conflict be resolved by adjusting speed *without turning*?
    - **Check: Can I accelerate?** Look at the `TCPA` and `dist_km`. Is there *enough time and space* to accelerate and cross *in front of* the other vessel safely?
        - **IF YES:** This is the preferred tactic.
        - **Action: 'Accelerate'**
    - **Check: Must I slow down?** If accelerating is not safe (threat is too close, TCPA is too low), will slowing down allow the vessel to pass safely ahead of you?
        - **IF YES:** This is the second-best tactic.
        - **Action: 'Reduce speed'**
    - **Last Resort (Course Change):** If and ONLY if a speed adjustment is clearly insufficient or unsafe (e.g., risk is imminent, DCPA is near zero), then you must alter course.
        - **Action: 'Alter course to starboard'** (preferred) or 'Pass astern'.
**Decision Focus:** Respond ONLY with a JSON array containing ONE object for the crossing vessel.

**Output Format Requirements:**
JSON object must have keys: "id", "situation", "role", "action".
1.  `"id"`: Integer ID.
2.  `"situation"`: Brief description.
3.  `"role"`: Role relative to immediate threat.
4.  `"action"`: ONE of the exact phrases below:
    - 'Alter course to starboard'
    - 'Alter course to port'
    - 'Reduce speed'
    - 'Pass astern'
    - 'Accelerate'
    - 'Maintain course and speed'

--- Current Vessel Data ---"
"""

# --- Data Population Logic (Identical) ---
    for v in vessels_to_describe:
        speed_kmh = (v.speed / pixels_per_km * 3600) if pixels_per_km > 0 else 0
        prompt += f"\n- id: {id(v)}, position: ({v.x:.1f}, {v.y:.1f}) px, heading: {math.degrees(v.heading):.1f}°, speed: {speed_kmh:.1f} km/h"
        prompt += "\n  Other vessels (Traffic):"
        other_vessels_found = False; threats = []
        for o in all_context_vessels:
            if o is v: continue
            dx, dy = o.x - v.x, o.y - v.y; dist_km = math.hypot(dx, dy) / pixels_per_km if pixels_per_km > 0 else 0
            rb = calculate_relative_bearing(v, o); sp = (o.speed / pixels_per_km * 3600) if pixels_per_km > 0 else 0
            tcpa, dcpa_km = calculate_cpa_details(v, o, pixels_per_km)
            threat_str = ( f"\n    - id: {id(o)}, pos: ({o.x:.1f},{o.y:.1f}) px, heading: {math.degrees(o.heading):.1f}°,"
                           f" speed: {sp:.1f} km/h, dist: {dist_km:.3f} km, relBearing: {rb:.1f}°" )
            cpa_info = ""
            if tcpa is not None and dcpa_km is not None and tcpa < 120:
                 cpa_info = f" (TCPA: {tcpa:.1f}s, DCPA: {dcpa_km:.3f}km)"
                 threat_str += cpa_info
            threats.append((tcpa if tcpa is not None else 9999, threat_str))
            other_vessels_found = True
        threats.sort()
        for _, threat_str in threats: prompt += threat_str
        if not other_vessels_found: prompt += "\n    - None"

    return prompt
