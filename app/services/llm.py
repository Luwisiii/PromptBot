from app.llm_client import get_client
from app.schemas.contract import CopilotDecision
from app.services.llm_repair import extract_json, repair_json_with_llm

MAX_RETRIES = 2


SYSTEM_PROMPT = """
You are PromptBot — a Prompt Compiler for multimedia generation.

Your job is to interpret the user's message and transform it into
a high-quality prompt for image, video, or audio generation.

The user may be vague, short, or conversational.
You must intelligently interpret their intent.

If the request is missing a CRITICAL detail that prevents you from
building a good prompt, you may ask ONE short clarification question
using the "ask" action.

Otherwise, always compile the best possible prompt from what you have.

You must output ONLY valid JSON:

{
  "action": "respond | ask | structured",
  "message": "string",
  "data": object | null
}
"""


EDIT_SYSTEM_PROMPT = """
You are PromptBot in EDIT MODE.

You are NOT creating a new prompt.
You are NOT redesigning the scene.
You are NOT adding new sections or fields.

You are ONLY editing the existing prompt text.

You will receive:
- ORIGINAL PROMPT
- USER CHANGE

CRITICAL RULES:

1) You MUST preserve the original structure of the prompt.
2) You MUST NOT add new keys or fields.
3) You MUST NOT reformat into a new schema.
4) You MUST NOT describe a new scene.
5) You ONLY modify words inside the original prompt.

If the original is a portrait, it must remain a portrait.
If the original is a scene, it must remain a scene.

You MUST return ONLY valid JSON in this EXACT format:

{
  "action": "respond",
  "message": "FULL updated prompt with edits applied",
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