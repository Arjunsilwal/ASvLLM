import os
import json
import re
from typing import Optional
from openai import OpenAI

# ─── CONFIG ────────────────────────────────────────────────────────────────────
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
DEEPSEEK_API_KEY_ENV = "DEEPSEEK_API_KEY"
DEEPSEEK_MODEL = "deepseek-chat"

YOUR_SITE_URL = "local_pygame_simulator"
YOUR_APP_NAME = "VesselSim_COLREGs_Test"

# DeepSeek pricing (per token)
INPUT_TOKEN_PRICE = 0.55 / 1_000_000
OUTPUT_TOKEN_PRICE = 2.19 / 1_000_000


# ─── UTILS ─────────────────────────────────────────────────────────────────────
def calculate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return prompt_tokens * INPUT_TOKEN_PRICE + completion_tokens * OUTPUT_TOKEN_PRICE


def _clean_response(content: str) -> str:
    # strip markdown fences
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    # drop stray "json" markers
    return re.sub(r'^(?:json)?\s*|\s*$', "", text,
                  flags=re.IGNORECASE | re.MULTILINE).strip()


# ─── CLIENT SETUP ───────────────────────────────────────────────────────────────
api_key = os.getenv(DEEPSEEK_API_KEY_ENV)
if not api_key:
    print(f"FATAL ERROR: Environment variable '{DEEPSEEK_API_KEY_ENV}' not set.")
    client = None
else:
    client = OpenAI(base_url=DEEPSEEK_BASE_URL, api_key=api_key)
    print(f"[useLLm] DeepSeek API key loaded from {DEEPSEEK_API_KEY_ENV}.")


# ─── ENTRYPOINT ────────────────────────────────────────────────────────────────
def get_llm_decision(prompt: str) -> Optional[str]:
    """
    Sends the prompt to DeepSeek and returns a pretty‐printed JSON string,
    or None on error.
    """
    if client is None:
        print("ERROR: DeepSeek client not initialized.")
        return None
    if not isinstance(prompt, str) or not prompt.strip():
        print("ERROR: Prompt must be a non‐empty string.")
        return None

    # show the prompt
    print("\n===== Prompt Sent to DeepSeek =====")
    print(prompt)
    print("===================================\n")

    try:
        resp = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
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
        print(f"Error: DeepSeek request failed: {e}")
        return None

    # extract content
    try:
        content = resp.choices[0].message.content
    except Exception as e:
        print(f"Error: Unexpected DeepSeek response structure: {e}")
        return None

    if not content:
        print("Error: Empty content in LLM response.")
        return None

    # if usage info is present, print estimated cost
    if getattr(resp, "usage", None):
        p_toks = resp.usage.prompt_tokens
        c_toks = resp.usage.completion_tokens
        cost = calculate_cost(p_toks, c_toks)
        print(f"[DeepSeek] Prompt tokens: {p_toks}, Completion tokens: {c_toks}, Estimated cost: ${cost:.6f}")

    # clean & debug-print
    cleaned = _clean_response(content)
    # try parsing
    try:
        data = json.loads(cleaned)
        return json.dumps(data, indent=2)
    except json.JSONDecodeError:
        print("Error: Failed to parse cleaned content as JSON.")
        print("Received:\n", cleaned)
        return None
