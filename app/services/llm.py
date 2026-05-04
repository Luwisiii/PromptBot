import json
from app.llm_client import get_client
from app.schemas.contract import CopilotDecision
from app.services.llm_repair import extract_json, repair_json_with_llm

MAX_RETRIES = 2


SYSTEM_PROMPT = """
You are PromptBot — a Prompt State Compiler for multimedia generation.

You maintain and evolve a persistent CREATIVE STATE.

You MUST ALWAYS treat "current_state" as the single source of truth.

If current_state exists:
- You MUST modify it
- You MUST NOT reset it
- You MUST NOT ignore it

If current_state is null:
- You must create a new state

OUTPUT FORMAT (STRICT):

{
  "action": "respond | ask | structured",
  "state": {
    "subject": "...",
    "composition": "...",
    "scene": "...",
    "style": ["..."],
    "mood": "...",
    "prompt": "FULL FINAL PROMPT STRING"
  },
  "data": null
}
"""


EDIT_SYSTEM_PROMPT = """
You are PromptBot in EDIT MODE.

You are PATCHING an existing STATE object.

CRITICAL RULES:

1) current_state is your ONLY source of truth
2) You MUST NOT recreate state from scratch
3) You MUST ONLY modify fields requested by user
4) You MUST preserve ALL other fields EXACTLY

Allowed modifications:
- subject (only if explicitly requested)
- composition
- scene
- style (append or replace if requested)
- mood
- prompt refinement

You MUST return the FULL updated state.

OUTPUT FORMAT (STRICT):

{
  "action": "respond",
  "state": {
    "subject": "...",
    "composition": "...",
    "scene": "...",
    "style": ["..."],
    "mood": "...",
    "prompt": "FULL UPDATED PROMPT"
  },
  "data": null
}
"""


def compile_prompt(prompt: str, edit_mode: bool = False, state: dict | None = None):
    client = get_client()
    system_prompt = EDIT_SYSTEM_PROMPT if edit_mode else SYSTEM_PROMPT

    user_payload = {
        "input": prompt,
        "current_state": state
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_payload)},
    ]

    last_content = None

    for _ in range(MAX_RETRIES):
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=messages,
            temperature=0.2,  
        )

        content = response.choices[0].message.content
        last_content = content

        try:
            data = extract_json(content)
            validated = CopilotDecision(**data)
            return validated.model_dump()
        except Exception:
            continue

    repaired = repair_json_with_llm(last_content, "invalid output")
    validated = CopilotDecision(**repaired)
    return validated.model_dump()