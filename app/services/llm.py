from app.llm_client import get_client
from app.schemas.contract import CopilotDecision
from app.services.llm_repair import extract_json, repair_json_with_llm

MAX_RETRIES = 2


SYSTEM_PROMPT = """
You are PromptBot — a Prompt Compiler for multimedia generation.

You convert user input into a SINGLE unified prompt string.

You do NOT output multiple fields like style, settings, or elements.

You ONLY output ONE final prompt inside "message".

You may infer structure internally, but NEVER expose it.

If missing critical info, you may ask a question.

OUTPUT FORMAT IS FIXED:

{
  "action": "respond | ask | structured",
  "message": "FINAL SINGLE PROMPT STRING ONLY",
  "data": null
}
"""

EDIT_SYSTEM_PROMPT = """
You are PromptBot in EDIT MODE.

You are NOT creating a new prompt.
You are NOT redesigning the scene.
You are NOT changing structure.

You are ONLY editing the TEXT inside the existing prompt.

You will receive:
- ORIGINAL PROMPT
- USER CHANGE

CRITICAL RULES:

1) You MUST preserve the original structure of the prompt EXACTLY.
2) You MUST NOT add or remove any sections.
3) You MUST NOT introduce new fields, keys, or schema.
4) You MUST NOT convert into structured breakdowns (no lists, no objects).
5) You MUST NOT reformat the prompt.

You are ONLY allowed to modify words inside the existing text.

OUTPUT RULE:

You MUST return ONLY valid JSON in EXACT format:

{
  "action": "respond",
  "message": "FULL updated prompt text only",
  "data": null
}
"""

def compile_prompt(prompt: str, edit_mode: bool = False):
    client = get_client()
    system_prompt = EDIT_SYSTEM_PROMPT if edit_mode else SYSTEM_PROMPT

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    last_content = None
    last_error = None

    for _ in range(MAX_RETRIES):
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=messages,
            temperature=0.7,
        )

        content = response.choices[0].message.content
        last_content = content
        
        try:
            data = extract_json(content)
            validated = CopilotDecision(**data)
            return validated.model_dump()
        except Exception as e:
            last_error = str(e)

    # Final repair pass (no scolding retries)
    repaired = repair_json_with_llm(last_content, last_error)
    validated = CopilotDecision(**repaired)
    return validated.model_dump()