import json
from app.llm_client import get_client


def extract_json(text: str) -> dict:
    if not text:
        raise ValueError("Empty LLM response")

    text = text.strip()

    # remove markdown
    if "```" in text:
        text = text.split("```")[-1].strip()

    # scan from end (prevents input echo bug)
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
You are a strict JSON repair engine.

Return ONLY valid JSON matching the required schema.

RULES:
- no markdown
- no explanation
- no extra keys
- must be valid JSON

ERROR:
{error}

BROKEN JSON:
{bad_json_text}
"""

    response = client.chat.completions.create(
        model="qwen/qwen-2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": "You repair JSON only."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        max_tokens=800
    )

    fixed = response.choices[0].message.content or ""

    # 🔥 reuse robust extractor
    return extract_json(fixed)