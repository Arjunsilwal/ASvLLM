import os
import re
import json
import pygame
import base64
from typing import Optional

# A placeholder for the fetch function
try:
    from js import fetch
except ImportError:
    print("Warning: 'js.fetch' not available. Using a placeholder. Install 'requests' for local use.")
    import requests
    from types import SimpleNamespace

    async def fetch(url, options):
        real_response = requests.post(url, headers=options.get('headers'), data=options.get('body'))
        mock_response = SimpleNamespace()
        mock_response.ok = real_response.status_code == 200
        mock_response.status = real_response.status_code
        _text = real_response.text
        def _json():
            try: return real_response.json()
            except json.JSONDecodeError: return {}
        async def text(): return _text
        async def json(): return _json()
        mock_response.text = text
        mock_response.json = json
        return mock_response

# --- CONFIGURATION for OpenAI ---
# Use the standard environment variable name for OpenAI keys
OPENAI_API_KEY_ENV = "GPT_API_KEY"

class VisionDecisionManager:
    """
    Handles sending a snapshot of the simulation to a multimodal LLM
    and returning a JSON decision. This version is configured for
    the OpenAI API.
    """

    def __init__(self, model_name: str = "gpt-4o"):
        self.model_name = model_name
        print(f"Initializing VisionDecisionManager for OpenAI (Model: {self.model_name})...")
        self.api_key = os.getenv(OPENAI_API_KEY_ENV)
        if not self.api_key:
            raise ValueError(f"FATAL: Environment variable '{OPENAI_API_KEY_ENV}' not set.")

        # API Endpoint for OpenAI Chat Completions ---
        self.api_url = "https://api.openai.com/v1/chat/completions"
        print("VisionDecisionManager is ready.")

    def _clean_json_response(self, content: str) -> Optional[str]:
        if not isinstance(content, str): return None
        match = re.search(r'```(json)?\s*(\[.*\])\s*```', content, re.DOTALL)
        if match: return match.group(2)
        start = content.find('[')
        end = content.rfind(']')
        if start != -1 and end != -1 and end > start: return content[start:end + 1]
        return None

    async def get_llm_decision_from_image(self, screen_surface: pygame.Surface, prompt: str) -> Optional[str]:
        print("\n--- Vision Manager: Processing image for LLM... ---")
        try:
            # 1. Convert Pygame surface to a base64 string
            image_filename = "temp_for_api.jpg"
            pygame.image.save(screen_surface, "temp_for_api.jpg")
            with open("temp_for_api.jpg", "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Headers for OpenAI ---
            # The API key must be sent in the 'Authorization' header as a Bearer token.
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Payload Structure for OpenAI ---
            # The payload uses a 'messages' array with a specific format for images.
            payload = {
                "model": self.model_name,
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ],
                    }
                ],
            }


            # Print only the image filename and the text prompt for clarity.
            print("--- DATA SENT TO LLM ---")
            print(f"Image File: {image_filename}")
            print("Text Prompt Sent:")
            print(prompt)
            # print("------------------------\n")
            # --- END OF LOGGING BLOCK ---

            # 3. Make the API call
            response = await fetch(self.api_url, {
                "method": 'POST',
                "headers": headers,
                "body": json.dumps(payload)
            })

            if not response.ok:
                error_text = await response.text()
                print(f"--- Vision API Error: {response.status} {error_text} ---")
                return "[]"

            result = await response.json()

            # --- FIX 4: Correct Response Parsing for OpenAI ---
            # The response text is located in a different place in the JSON.
            raw_text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
            clean_json = self._clean_json_response(raw_text)

            if not clean_json:
                print("--- Vision Warning: Could not extract valid JSON from LLM response. ---")
                print("Raw response was:", raw_text)
                return "[]"

            return clean_json

        except Exception as e:
            print(f"Error during Vision API call execution: {e}")
            return "[]"