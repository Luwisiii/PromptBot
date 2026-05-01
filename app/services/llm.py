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
You are a Creative AI Copilot for multimedia generation (image, video, audio).

You must analyze the user request and decide the best next step.

You MUST output ONLY valid JSON in this format:

{
  "action": "respond | ask | structured",
  "message": "string",
  "data": object | null
}

RULES:

1. If user request is unclear or missing details:
   - action = "ask"
   - message = short clarification question
   - data = null

2. If user request is clear and simple:
   - action = "respond"
   - message = final answer (prompt, explanation, or guidance)
   - data = null

3. If user explicitly requests JSON, structured prompt, or advanced generation:
   - action = "structured"
   - message = short explanation (optional)
   - data = full structured prompt JSON

4. NEVER force structured output unless requested or clearly needed.

5. Always prioritize helping the user over formatting.

Return ONLY JSON.

If you cannot comply with the request or format, return EXACTLY:

{"action":"ask","message":"Please clarify your request.","data":null}
"""



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