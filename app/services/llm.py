import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError as PydanticError

from app.schemas.llm_contract import MediaSpec
from app.services.validator import validate_media_json

load_dotenv()

MAX_RETRIES = 3

SYSTEM_PROMPT = """
You are a JSON compiler.

Convert messy user prompts into STRICT JSON using this contract.

You MUST fill ALL fields with smart defaults.

SCHEMA EXAMPLE:

If type = "image":

{
  "type": "image",
  "prompt": "...",
  "negative_prompt": "...",
  "style": "...",
  "media": {
    "resolution": "1024x1024",
    "aspect_ratio": "1:1",
    "format": "png"
  },
  "quality": {
    "steps": 30,
    "guidance": 7.5,
    "upscale": false
  },
  "extras": {}
}

If type = "video":

{
  "type": "video",
  "prompt": "...",
  "negative_prompt": "...",
  "style": "...",
  "media": {
    "resolution": "1920x1080",
    "aspect_ratio": "16:9",
    "duration": 8,
    "fps": 24,
    "format": "mp4"
  },
  "quality": {
    "motion_strength": 0.7,
    "stability": 0.6,
    "camera_motion": "static"
  },
  "extras": {}
}

If type = "audio":

{
  "type": "audio",
  "prompt": "...",
  "negative_prompt": null,
  "style": "...",
  "media": {
    "duration": 10,
    "format": "mp3",
    "sample_rate": 44100
  },
  "quality": {
    "voice_clarity": 0.8,
    "background_noise": 0.2
  },
  "extras": {}
}

Rules:
- Output ONLY JSON
- No explanation
- No markdown
- No missing keys
"""

# -------------------------
# OpenRouter client
# -------------------------
def get_client():
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY missing in .env")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
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

            # ✅ PASSED — safe to use
            return data

        except (PydanticError, Exception) as e:
            # 🔁 Self-healing repair loop
            user_message = f"""
The JSON you returned is INVALID.

Errors:
{str(e)}

Fix the JSON to match the required schema EXACTLY.
Return JSON only.

Original user prompt: {prompt}
"""

    raise ValueError("LLM failed to produce valid JSON after retries.")