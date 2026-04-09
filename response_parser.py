import json
import enum

# Maneuver enum definition
class Maneuver(enum.IntEnum):
    MAINTAIN_COURSE_SPEED = 0
    ALTER_COURSE_STARBOARD = 1
    ALTER_COURSE_PORT = 2
    REDUCE_SPEED = 3
    PASS_ASTERN = 4
    ACCELERATE = 5

def parse_llm_response_for_all(response_json_string: str):
    """
    Parses a JSON array response from LLM and maps actions to Maneuver enum.
    Uses expanded keyword matching to handle stylistic differences between models.
    """
    try:
        # Clean up common LLM markdown artifacts if present
        cleaned_json = response_json_string.strip().replace('```json', '').replace('```', '')
        data = json.loads(cleaned_json)
        if not isinstance(data, list):
            return []
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON response.")
        return []

    results = []
    for entry in data:
        raw_id = entry.get("id")
        try:
            vid = int(raw_id)
        except (ValueError, TypeError):
            continue

        action_str = (entry.get("action") or "").lower()

        # --- REFINED KEYWORD MAPPING ---
        # Order matters here: Check for specific maneuvers before generic ones.
        if any(x in action_str for x in ["astern", "pass behind"]):
            m = Maneuver.PASS_ASTERN
        elif any(x in action_str for x in ["starboard", "right", "stbd"]):
            m = Maneuver.ALTER_COURSE_STARBOARD
        elif any(x in action_str for x in ["port", "left"]):
            m = Maneuver.ALTER_COURSE_PORT
        elif any(x in action_str for x in ["reduce", "slow", "decelerate", "stop"]):
            m = Maneuver.REDUCE_SPEED
        elif any(x in action_str for x in ["accelerate", "increase speed", "speed up", "fast"]):
            m = Maneuver.ACCELERATE
        elif any(x in action_str for x in ["maintain", "keep course", "steady"]):
            m = Maneuver.MAINTAIN_COURSE_SPEED
        else:
            # Fallback for "Keep clear" or "Avoid collision" usually implies Starboard
            if any(x in action_str for x in ["keep clear", "avoid"]):
                m = Maneuver.ALTER_COURSE_STARBOARD
            else:
                m = Maneuver.MAINTAIN_COURSE_SPEED

        results.append({
            "id": vid,
            "action": entry.get("action"),
            "maneuver": m,
            "situation": entry.get("situation", "N/A"),
            "role": entry.get("role", "N/A"),
            "explanation": entry.get("explanation", "No explanation.")
        })
    return results