import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


def main():
    load_dotenv(".env")

    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("DEEPSEEK_API_KEY is missing from .env or environment.")
        sys.exit(1)

    client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com/v1")

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "Reply with exactly: OK"}],
            max_tokens=5,
            temperature=0,
        )
    except Exception as exc:
        print("DeepSeek API test failed.")
        print(exc)
        sys.exit(1)

    content = response.choices[0].message.content if response.choices else ""
    print("DeepSeek API test succeeded.")
    print(f"Response: {content}")


if __name__ == "__main__":
    main()
