import json
from app.llm_client import get_client
from app.schemas.contract import CopilotDecision
from app.services.llm_repair import extract_json, repair_json_with_llm

MAX_RETRIES = 2

SYSTEM_PROMPT = """
You are PromptBot — a Prompt State Compiler.

You receive:
- user input
- current_state (may be null)

Your job is to intelligently evolve a CREATIVE STATE for multimedia generation.

Guidelines:

• If current_state exists, treat it as the source of truth and evolve it
• You are allowed to improve, expand, reorganize, and enrich the state
• You are NOT limited to shallow edits
• The final "prompt" must be a rich, production-ready generation prompt
• Do not be mechanical. Think creatively.

Return ONLY a valid JSON object that matches the schema.
"""


def compile_prompt(prompt: str, state: dict | None = None):
    client = get_client()

    user_payload = {
        "input": prompt,
        "current_state": state
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
          temperature=0.7,
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