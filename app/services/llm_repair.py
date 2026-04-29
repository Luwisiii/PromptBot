import os
from openai import OpenAI
import json


def get_client():
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )


def repair_json_with_llm(bad_json: dict, error: str):
    """
    Last resort: fix broken payload using LLM
    """

    client = get_client()

    prompt = f"""
You are a strict JSON repair engine.

Fix this JSON to match the required schema EXACTLY.

RULES:
- Output ONLY JSON
- No markdown
- No explanation
- Must be valid JSON
- Must preserve intent

ERROR:
{error}

BROKEN JSON:
{json.dumps(bad_json, indent=2)}
"""

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[
            {"role": "system", "content": "You repair invalid JSON structures."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    
    content = response.choices[0].message.content

    return json.loads(content)