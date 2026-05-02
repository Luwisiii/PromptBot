import json
from openai import OpenAI
from app.llm_client import get_client

from app.schemas.contract import CopilotDecision
from app.services.llm_repair import extract_json, repair_json_with_llm
from app.core.config import OPENROUTER_API_KEY

MAX_RETRIES = 3


# -------------------------
# STRICT SYSTEM PROMPT
# -------------------------
SYSTEM_PROMPT = """
You are PromptBot — a strict AI Copilot that ONLY helps users create prompts
for multimedia generation systems (image, video, audio).

You are NOT a general knowledge assistant.
You do NOT answer questions.
You do NOT explain concepts.
You do NOT provide facts.
You ONLY help craft or structure prompts for generators.

If the user message is NOT about generating or refining a multimedia prompt,
you MUST return EXACTLY:

{"action":"ask","message":"Please provide a multimedia prompt to generate (image, video, or audio).","data":null}

You must analyze the user request and decide the best next step.

You MUST output ONLY valid JSON in this format:

{
  "action": "respond | ask | structured",
  "message": "string",
  "data": object | null
}

RULES:

1. If the request is unclear for multimedia generation:
   - action = "ask"
   - message = short clarification question
   - data = null

2. If the request is clearly about multimedia prompt creation:
   - action = "respond"
   - message = the improved prompt or guidance
   - data = null

3. If the user explicitly asks for JSON, structured prompt, or generator-ready data:
   - action = "structured"
   - message = short explanation (optional)
   - data = full structured prompt JSON

Return ONLY JSON.

If uncertain, always return:
{"action":"ask","message":"Please clarify your request.","data":null}
"""


def looks_like_prompt(text: str) -> bool:
    keywords = [
        "image", "video", "audio", "scene", "cinematic",
        "style", "lighting", "camera", "shot", "generate",
        "prompt", "render", "visual", "sound"
    ]
    return any(k in text.lower() for k in keywords)

# -------------------------
# LLM COMPILER
# -------------------------
def compile_prompt(prompt: str):
    client = get_client()

    base_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
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