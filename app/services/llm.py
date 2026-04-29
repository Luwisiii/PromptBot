import json
import re
from openai import OpenAI
from pydantic import ValidationError as PydanticError

from app.schemas.llm_contract import MediaSpec, GenerationPrompt
from app.services.validator import validate_media_json
from app.core.config import OPENROUTER_API_KEY

MAX_RETRIES = 3
SYSTEM_PROMPT = """
You are a JSON compiler.

Convert messy prompts into STRICT structured JSON.

RULE:

You MUST ALSO generate:

generation_prompt:
- structured hierarchical prompt for downstream generator use
- must include:
  - task
  - goal
  - identity_handling (if applicable)
  - scene
  - environment
  - lighting
  - camera
  - style
  - generation_prompt (final prompt string + negative_prompt)
  - variants (optional)

This field is REQUIRED.

Return ONLY valid JSON.
"""


# -------------------------
# OpenRouter client
# -------------------------
def get_client():
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY missing in environment")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


# -------------------------
# Extract JSON safely
# -------------------------
def safe_json_parse(text: str):
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise ValueError(f"Invalid JSON from LLM:\n{text}")


# -------------------------
# 🔥 LLM Firewall Compiler
# -------------------------
def compile_prompt(prompt: str, target: str):
    client = get_client()

    user_message = f"""
Type: {target}
Prompt: {prompt}
"""

    for attempt in range(MAX_RETRIES):
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content
        data = safe_json_parse(content)

        try:
            # 1️⃣ Pydantic structure check
            MediaSpec(**data)

            # 2️⃣ JSON Schema strict validation
            validate_media_json(data)

            # ✅ SUCCESS
            return data

        except (PydanticError, Exception) as e:
            # 🔁 Self-healing retry prompt
            user_message = f"""
The JSON you returned is INVALID.

Errors:
{str(e)}

Fix the JSON to match the required schema EXACTLY.
Return JSON only.

Original prompt: {prompt}
"""

    raise ValueError("LLM failed to produce valid JSON after retries.")