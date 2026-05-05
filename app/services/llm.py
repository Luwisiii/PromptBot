import json
from app.llm_client import get_client
from app.schemas.contract import CopilotDecision
from app.services.llm_repair import extract_json, repair_json_with_llm

MAX_RETRIES = 2


# 🔥 STRICT SCHEMA-BASED PROMPT (FIXED)
SYSTEM_PROMPT = """
You are PromptBot — a strict Prompt State Compiler.

You MUST output ONLY valid JSON matching this schema:

{
  "action": "ask | respond | structured",
  "state": {
    "subject": string | null,
    "composition": string | null,
    "scene": string | null,
    "style": list[string] | null,
    "mood": string | null,
    "prompt": string | null
  },
  "data": object | null
}

RULES:
- NEVER include input, current_state, or any extra keys
- ALWAYS return action, state, data
- state must follow schema exactly
- If unsure, use action = "respond"
"""


# 🔥 TOKEN SAFETY (IMPORTANT FIX)
def trim_state(state: dict | None):
    if not state:
        return None

    return {
        "subject": state.get("subject"),
        "composition": state.get("composition"),
        "scene": state.get("scene"),
        "style": (state.get("style") or [])[:5],
        "mood": state.get("mood"),
        # 🚨 prevent recursive prompt explosion
        "prompt": None
    }


def compile_prompt(prompt: str, state: dict | None = None):
    client = get_client()

    user_payload = {
        "input": prompt,
        "current_state": trim_state(state)
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_payload)},
    ]

    last_content = ""

    for _ in range(MAX_RETRIES):
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-coder-32b-instruct",  # ✅ correct OpenRouter ID
            messages=messages,
            temperature=0.6,
            max_tokens=1200
        )

        content = response.choices[0].message.content or ""
        last_content = content

        try:
            data = extract_json(content)
            validated = CopilotDecision(**data)
            return validated.model_dump()
        except Exception:
            continue

    # 🔥 fallback repair path
    repaired = repair_json_with_llm(last_content, "invalid output")
    validated = CopilotDecision(**repaired)

    return validated.model_dump()