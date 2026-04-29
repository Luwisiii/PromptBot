import json
from openai import OpenAI
from json import JSONDecodeError

from app.schemas.llm_contract import GenerationPrompt
from app.core.config import OPENROUTER_API_KEY

MAX_RETRIES = 3


# -------------------------
# STRICT SYSTEM PROMPT
# -------------------------
SYSTEM_PROMPT = """
You are a SENIOR prompt engineer and visual director.

Your job is NOT to copy the input.

You MUST EXPAND and ENRICH the prompt into a detailed creative production brief.

RULES:
- You MUST infer missing details creatively
- You MUST NOT leave objects empty
- You MUST NOT return shallow or empty fields
- Every field must contribute meaningful creative direction
- If information is missing, you MUST intelligently guess

OUTPUT ONLY VALID JSON.

SCHEMA:

{
  "task": string,
  "goal": string,

  "identity_handling": object | null,

  "scene": {
    "description": string,
    "elements": array
  },

  "environment": {
    "time": string,
    "location_type": string,
    "atmosphere": string
  },

  "lighting": {
    "type": string,
    "intensity": string,
    "color": string
  },

  "camera": {
    "shot_type": string,
    "lens": string,
    "angle": string
  },

  "style": {
    "genre": string,
    "influences": array,
    "render_type": string
  },

  "generation_prompt": {
    "prompt": string,
    "negative_prompt": string
  },

  "variants": array | null
}

CRITICAL:
- NEVER return empty objects
- ALWAYS expand creatively
- ALWAYS infer details for cyberpunk, cinematic, etc.
- RETURN ONLY JSON
"""


# -------------------------
# CLIENT
# -------------------------
def get_client():
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY missing")

    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


# -------------------------
# SAFE PARSER (NO REGEX)
# -------------------------
def safe_json_parse(text: str):

    # 🧠 STEP 1: guard empty response
    if not text or not text.strip():
        raise ValueError("LLM returned empty response")

    text = text.strip()

    # 🧠 STEP 2: remove markdown fences if present
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("{"):
                text = part
                break

    # 🧠 STEP 3: try strict JSON parse
    try:
        return json.loads(text)

    except JSONDecodeError:

        # 🧠 STEP 4: last-resort extraction (SAFE, not regex greedy)
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            raise ValueError(f"NO JSON FOUND IN RESPONSE:\n{text}")

        candidate = text[start:end + 1]

        try:
            return json.loads(candidate)
        except Exception:
            raise ValueError(f"INVALID JSON AFTER RECOVERY:\n{text}")

# -------------------------
# LLM COMPILER
# -------------------------
def compile_prompt(prompt: str, target: str):
    client = get_client()

    user_message = f"""
TYPE: {target}
PROMPT: {prompt}
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
        if not content:
            raise ValueError("EMPTY LLM RESPONSE")

        print("LLM RAW OUTPUT:", content)
        data = safe_json_parse(content)

        try:
            # ONLY structural validation
            validated = GenerationPrompt(**data)

            return validated.model_dump()

        except Exception as e:

            user_message = f"""
Your previous JSON is INVALID.

FIX STRICTLY:

ERROR:
{str(e)}

OUTPUT MUST MATCH SCHEMA EXACTLY.

BAD OUTPUT:
{json.dumps(data, indent=2)}

Return ONLY valid JSON.
"""

    raise ValueError("LLM failed after retries")