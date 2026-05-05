import json
from app.llm_client import get_client


def extract_json(text: str) -> dict:
    if not text:
        raise ValueError("Empty LLM response")

    text = text.strip()

    if "```" in text:
        parts = text.split("```")
        text = parts[-1].strip()

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
Fix this JSON EXACTLY.

RULES:
- Only JSON output
- No markdown
- No explanation
- Must match schema

ERROR:
{error}

BROKEN:
{bad_json_text}
"""

    response = client.chat.completions.create(
        model="qwen/qwen-2.5-coder-32b-instruct", 
        messages=[
            {"role": "system", "content": "Strict JSON fixer."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=800,
    )

    fixed = response.choices[0].message.content or ""

    return extract_json(fixed)