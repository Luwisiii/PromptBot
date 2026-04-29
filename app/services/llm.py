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
You are a STRICT JSON generator.

Return ONLY valid JSON. No markdown. No explanation.

OUTPUT MUST MATCH THIS EXACT SCHEMA:

{
  "task": string,
  "goal": string,

  "identity_handling": object | null,

  "scene": object,
  "environment": object | null,
  "lighting": object | null,
  "camera": object | null,
  "style": object | null,

  "generation_prompt": {
    "prompt": string,
    "negative_prompt": string
  },

  "variants": array | null
}

RULES:
- ALL keys must exist
- Use null if missing
- NO extra keys
- VALID JSON ONLY
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
    try:
        return json.loads(text)
    except JSONDecodeError:
        text = text.strip()

        # remove markdown fences safely
        if text.startswith("```"):
            text = text.split("```")[1]

        return json.loads(text)


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