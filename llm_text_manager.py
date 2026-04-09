import os
import re
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from env_utils import load_project_env


class LLMTextManager:
    def __init__(self, provider: str = "openai"):
        print(f"Initializing LLMTextManager for provider: {provider}...")
        load_project_env()
        self.provider = provider.lower()
        self.llm = self._setup_llm(self.provider)

    def _setup_llm(self, provider: str):
        if provider == "openai":
            return ChatOpenAI(model="gpt-5.2-2025-12-11", api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
        elif provider in ["claude", "anthropic"]:
            return ChatAnthropic(model="claude-sonnet-4-5-20250929", anthropic_api_key=os.getenv("CLAUDE_API_KEY"),
                                 temperature=0)
        elif provider == "deepseek":
            return ChatOpenAI(model="deepseek-chat", api_key=os.getenv("DEEPSEEK_API_KEY"),
                              base_url="https://api.deepseek.com/v1", temperature=0)
        raise ValueError(f"Unsupported provider: {provider}")

    async def get_llm_decision_standard(self, prompt: str) -> str:
        print(f"\n--- LLM Text Manager ({self.provider}): Sending prompt... ---")
        try:
            # 1. Force convert the entire string to ASCII, ignoring any non-ASCII characters
            # This is the 'nuclear option' for the \u201c error
            safe_prompt = str(prompt).encode("ascii", "ignore").decode("ascii")

            # 2. If the string started with a smart quote, it's now gone.
            # We ensure there is still a prompt to send.
            if not safe_prompt.strip():
                safe_prompt = "Provide a navigation decision based on COLREGs."

            # 3. Call the LLM
            response = await self.llm.ainvoke(safe_prompt)
            return self._clean_json_response(response.content)
        except Exception as e:
            # If it STILL fails here, the error is in the API Key or Headers, not the prompt
            print(f"Text API Error ({self.provider}): {e}")
            return "[]"

    def _clean_json_response(self, text: str) -> str:
        if not text: return "[]"
        json_match = re.search(r'```(?:json)?\s*(\[.*\])\s*```', text, re.DOTALL)
        if json_match: return json_match.group(1).strip()
        array_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if array_match: return array_match.group(0).strip()
        return "[]"
