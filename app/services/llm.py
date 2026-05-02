import json
from openai import OpenAI
from app.llm_client import get_client

from app.schemas.contract import CopilotDecision
from app.services.llm_repair import extract_json, repair_json_with_llm

MAX_RETRIES = 3


# -------------------------
# CREATION SYSTEM PROMPT
# -------------------------
SYSTEM_PROMPT = """
You are PromptBot — a strict AI Copilot that ONLY helps users create prompts
for multimedia generation systems (image, video, audio).

You are NOT a general knowledge assistant.

If the user message is NOT about generating or refining a multimedia prompt,
you MUST return EXACTLY:

{"action":"ask","message":"Please provide a multimedia prompt to generate (image, video, or audio).","data":null}

You MUST output ONLY valid JSON in this format:

{
  "action": "respond | ask | structured",
  "message": "string",
  "data": object | null
}
"""


# -------------------------
# ✨ EDIT SYSTEM PROMPT (THE FIX)
# -------------------------
EDIT_SYSTEM_PROMPT = """
You are PromptBot in EDIT MODE.

The user is MODIFYING an existing multimedia prompt.

You will be given:
- The original prompt
- The user change

Your job is to APPLY the change with MINIMAL edits.

You MUST NOT ask for a new prompt.
You MUST NOT reject the request.

You MUST return ONLY valid JSON:

{
  "action": "respond",
  "message": "the fully updated prompt",
  "data": null
}
"""


# -------------------------
# LLM COMPILER
# -------------------------
def compile_prompt(prompt: str, edit_mode: bool = False):
    client = get_client()

    system_prompt = EDIT_SYSTEM_PROMPT if edit_mode else SYSTEM_PROMPT

    base_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    last_error = None
    last_content = None

    for attempt in range(MAX_RETRIES):
        messages = list(base_messages)

        if last_error:
            messages.append({
                "role": "user",
                "content": f"""
Your previous output was invalid JSON.

Return ONLY valid JSON in this format:

{{
  "action": "respond | ask | structured",
  "message": "string",
  "data": object | null
}}

Error:
{last_error}
"""
            })

        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=messages,
            temperature=0.0,
        )

        content = response.choices[0].message.content
        last_content = content

        try:
            data = extract_json(content)
            validated = CopilotDecision(**data)
            return validated.model_dump()

        except Exception as e:
            last_error = str(e)

    # LAST RESORT — LLM REPAIR
    try:
        repaired = repair_json_with_llm(last_content, last_error)
        validated = CopilotDecision(**repaired)
        return validated.model_dump()
    except Exception:
        raise ValueError("LLM failed after retries and repair")