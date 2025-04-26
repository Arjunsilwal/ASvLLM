import os
import json
import re
from typing import Optional
from openai import OpenAI  # this import should work once you have the 'openai' package installed

# --- Config ---
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_ENV_VAR = "OPENROUTER_API_KEY"
OPENROUTER_MODEL = "meta-llama/llama-4-maverick:free"
YOUR_SITE_URL = "local_pygame_simulator"
YOUR_APP_NAME = "VesselSim_COLREGs_Test"

# --- Initialize OpenRouter client ---
api_key = os.getenv(OPENROUTER_API_KEY_ENV_VAR)
if not api_key:
    print(f"FATAL ERROR: Environment variable '{OPENROUTER_API_KEY_ENV_VAR}' not set.")
    client = None
else:
    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )
    print(f"API Key loaded from {OPENROUTER_API_KEY_ENV_VAR}.")


def get_llm_decision(prompt: str) -> Optional[str]:
    """
    Sends the prompt to OpenRouter via the OpenAI client.
    Expects a JSON-object response (stringified).
    Returns the pretty-printed JSON string, or None on error.
    """
    if client is None:
        print("ERROR: OpenRouter client not initialized.")
        return None

    if not isinstance(prompt, str):
        print(f"ERROR: Prompt must be a string, got {type(prompt)}")
        return None

    # --- Debug-print the prompt ---
    print("\n===== Prompt Sent to LLM =====")
    print(prompt)
    print("==============================\n")

    try:
        # call the chat completion endpoint
        completion = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[{"role": "user", "content": prompt}],
            extra_headers={
                "HTTP-Referer": YOUR_SITE_URL,
                "X-Title": YOUR_APP_NAME,
            },
            max_tokens=350,
            temperature=0.1,
            stream=False,
        )
    except Exception as e:
        # catch *all* errors from the client
        print(f"Error: LLM request failed: {e}")
        return None

    # extract the raw content
    try:
        content = completion.choices[0].message.content
    except Exception as e:
        print(f"Error: Unexpected completion structure: {e}")
        return None

    if not content:
        print("Error: Empty content in LLM response.")
        return None

    # --- Clean out Markdown fences or stray 'json' tokens ---
    cleaned = content.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    cleaned = re.sub(r'^(?:json)?\s*|\s*$', "", cleaned, flags=re.IGNORECASE | re.MULTILINE).strip()

    # --- Try parsing as JSON ---
    try:
        data = json.loads(cleaned)
        pretty = json.dumps(data, indent=2)
        return pretty
    except json.JSONDecodeError:
        print("Error: Failed to parse cleaned content as JSON.")
        print("Received:\n", cleaned)
        return None
