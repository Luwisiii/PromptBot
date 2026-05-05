import json
from app.llm_client import get_client


def extract_json(text: str) -> dict:
    if not text:
        raise ValueError("Empty LLM response")

    text = text.strip()

    # remove markdown blocks
    if "```" in text:
        text = text.split("```")[-1].strip()

    # scan backwards for valid JSON start
    for i in range(len(text) - 1, -1, -1):
        if text[i] == "{":
            candidate = text[i:]
            try:
                return json.loads(candidate)
            except Exception:
                continue

    raise ValueError(f"No valid JSON found in:\n{text}")


def repair_json_with_llm(bad_json_text: str, error: str):
    client = get_client()

    prompt = f"""
Fix this JSON strictly.

RULES:
- Output ONLY valid JSON
- No markdown
- No explanation
- Must match schema exactly
- Replace missing values with null
- NEVER use empty strings

ERROR:
{error}

BROKEN JSON:
{bad_json_text}
"""

    response = client.chat.completions.create(
        model="qwen/qwen-2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": "You are a strict JSON validator."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=800
    )

    fixed = response.choices[0].message.content or ""
    return extract_json(fixed)