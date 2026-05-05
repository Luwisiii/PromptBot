import json
from app.llm_client import get_client
from app.schemas.contract import CopilotDecision
from app.services.llm_repair import extract_json, repair_json_with_llm

MAX_RETRIES = 2


SYSTEM_PROMPT = """
You are PromptBot — a Prompt State Compiler.

You evolve a compact creative state for multimedia generation.

Rules:
- Keep state SMALL and EFFICIENT
- Do NOT repeat long prompts in state
- You may enrich meaning but avoid token bloat
- Always return valid JSON matching schema
"""


def trim_state(state: dict | None):
    if not state:
        return None

    return {
        "subject": state.get("subject"),
        "composition": state.get("composition"),
        "scene": state.get("scene"),
        "style": (state.get("style") or [])[:5],
        "mood": state.get("mood"),
        # 🚨 prevent token explosion
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

    last_content = None

    for _ in range(MAX_RETRIES):
        response = client.chat.completions.create(
            model="qwen/qwen-2.5-coder-32b-instruct", 
            messages=messages,
            temperature=0.6,
            max_tokens=1200,  # 🔥 prevents OpenRouter 402
        )

        content = response.choices[0].message.content or ""
        last_content = content

        try:
            data = extract_json(content)
            validated = CopilotDecision(**data)
            return validated.model_dump()
        except Exception:
            continue

    repaired = repair_json_with_llm(last_content, "invalid output")

    # 🔥 second safety validation
    validated = CopilotDecision(**repaired)
    return validated.model_dump()