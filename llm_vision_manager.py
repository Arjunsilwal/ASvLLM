import os
import re
import base64
import pygame
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from env_utils import load_project_env

class LLMVisionManager:
    def __init__(self, provider: str = "openai"):
        load_project_env()
        self.provider = provider.lower()
        self.llm = self._setup_llm(self.provider)

    def _setup_llm(self, provider: str):
        if provider == "openai":
            return ChatOpenAI(model="gpt-5.2-2025-12-11", api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
        elif provider in ["claude", "anthropic"]:
            return ChatAnthropic(model="claude-sonnet-4-5-20250929", anthropic_api_key=os.getenv("CLAUDE_API_KEY"), temperature=0)
        elif provider == "deepseek":
            return ChatOpenAI(
                model="deepseek-chat",
                api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com",
                temperature=0
            )
        raise ValueError(f"Unsupported provider: {provider}")

    async def get_llm_decision_from_image(self, screen_surface: pygame.Surface, prompt: str) -> str:
        try:
            # --- DEEPSEEK FALLBACK ---
            if self.provider == "deepseek":
                print("--- DeepSeek: Falling back to History + Prompt (Text-Only) ---")
                response = await self.llm.ainvoke(prompt)
                return self._clean_json_response(response.content)

            # Capture and encode image for OpenAI/Claude
            temp_path = "temp_vision.jpg"
            pygame.image.save(screen_surface, temp_path)
            with open(temp_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            # Construct Multimodal Message
            if self.provider == "openai":
                message = HumanMessage(content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}},
                ])
            else: # Claude
                message = HumanMessage(content=[
                    {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": img_b64}},
                    {"type": "text", "text": prompt},
                ])

            response = await self.llm.ainvoke([message])
            return self._clean_json_response(response.content)
        except Exception as e:
            print(f"Vision API Error ({self.provider}): {e}")
            return "[]"

    def _clean_json_response(self, text: str) -> str:
        if not text: return "[]"
        json_match = re.search(r'```(?:json)?\s*(\[.*\])\s*```', text, re.DOTALL)
        if json_match: return json_match.group(1).strip()
        array_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if array_match: return array_match.group(0).strip()
        return "[]"
