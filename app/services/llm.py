import json
from app.llm_client import get_client
from app.schemas.contract import CopilotDecision
from app.services.llm_repair import extract_json, repair_json_with_llm

MAX_RETRIES = 2


# 🔥 HARD STRICT SCHEMA PROMPT (FINAL FIX)
SYSTEM_PROMPT = """
You are PromptBot — a deterministic JSON state compiler.

You MUST output ONLY valid JSON.

ABSOLUTE RULES:

1. Output must be valid JSON (no partial output allowed)
2. NEVER stop mid-field
3. NEVER use empty strings ("") → use null instead
4. NEVER omit any key inside state
5. NEVER include input or current_state
6. ALWAYS complete full JSON before responding

STRICT OUTPUT FORMAT:

{
  "action": "ask | respond | structured",
  "state": {
    "subject": string or null,
    "composition": string or null,
    "scene": string or null,
    "style": array of strings or null,
    "mood": string or null,
    "prompt": string or null
  },
  "data": object or null
}

FIELD RULES:
- If unknown → null (NEVER "")
- style MUST always be array or null
- ALL fields must always exist
"""


# 🔥 SAFE INPUT NORMALIZER
def normalize_input(prompt: str):
    return prompt.strip()


# 🔥 SAFE STATE TRIM (prevents token explosion)
def trim_state(state: dict | None):
    if not state:
        return None

    return {
        "subject": state.get("subject"),
        "composition": state.get("composition"),
        "scene": state.get("scene"),
        "style": (state.get("style") or [])[:5],
        "mood": state.get("mood"),
        "prompt": None  # 🚨 prevents recursion explosion
    }


# 🔥 SANITIZER (CRITICAL FIX FOR YOUR BUG)
def sanitize_state(state: dict | None):
    if not state:
        return state

    return {
        "subject": state.get("subject") or None,
        "composition": state.get("composition") or None,
        "scene": state.get("scene") or None,

        # FIX: enforce correct type strictly
        "style": state.get("style") if isinstance(state.get("style"), list) else None,

        "mood": state.get("mood") or None,
        "prompt": state.get("prompt") or None,
    }


def compile_prompt(prompt: str, state: dict | None = None):
    client = get_client()

    user_payload = {
        "input": normalize_input(prompt),
        "current_state": trim_state(state)
    }

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(user_payload)},
    ]

    last_content = ""

    for _ in range(MAX_RETRIES):
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-coder-32b-instruct",
            messages=messages,
            temperature=0.1,   # 🔥 stability boost (IMPORTANT)
            max_tokens=1200
        )

        content = response.choices[0].message.content or ""
        last_content = content

        try:
            data = extract_json(content)
            validated = CopilotDecision(**sanitize_state(data))
            return validated.model_dump()
        except Exception:
            continue

    # 🔥 fallback repair path
    repaired = repair_json_with_llm(last_content, "invalid output")
    validated = CopilotDecision(**sanitize_state(repaired))

    return validated.model_dump()