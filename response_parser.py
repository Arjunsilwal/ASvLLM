import json
import enum


# Maneuver enum definition
class Maneuver(enum.IntEnum):
    MAINTAIN_COURSE_SPEED = 0
    ALTER_COURSE_STARBOARD = 1
    ALTER_COURSE_PORT = 2
    REDUCE_SPEED = 3
    PASS_ASTERN = 4


def parse_llm_response_for_all(response_json_string: str):
    """
    Parses a JSON array response from LLM and maps actions to Maneuver enum.
    More robust mapping for compound action strings.
    """
    try:
        data = json.loads(response_json_string)
        if not isinstance(data, list):
            print("Warning: Expected a JSON array but got:", data)
            return []
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON: {response_json_string}")
        return []

    results = []
    for entry in data:
        raw_id = entry.get("id")
        try:
            vid = int(raw_id)
        except (ValueError, TypeError):
            print(f"Warning: invalid id '{raw_id}', skipping entry")
            continue

        action_str = entry.get("action", "").lower()
        # robust normalization for mapping
        if ("alter course to starboard" in action_str
                or "altercoursestarboard" in action_str
                or "alter course or slow down" in action_str):
            m = Maneuver.ALTER_COURSE_STARBOARD
        elif "alter course to port" in action_str or "altercourseport" in action_str:
            m = Maneuver.ALTER_COURSE_PORT
        elif "reduce speed" in action_str or "reducespeed" in action_str:
            m = Maneuver.REDUCE_SPEED
        elif "pass astern" in action_str or "passastern" in action_str:
            m = Maneuver.PASS_ASTERN
        else:
            m = Maneuver.MAINTAIN_COURSE_SPEED

        results.append({
            "id": vid,
            "action": entry.get("action"),
            "maneuver": m,
            "situation": entry.get("situation"),
            "role": entry.get("role")
        })
    return results
