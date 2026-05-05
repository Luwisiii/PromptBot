import json
from json import JSONDecodeError
from app.llm_client import get_client


def extract_json(text: str) -> dict:
    """
    Extract the LAST valid JSON object from LLM text.
    This avoids grabbing the user payload echoed by the model.
    """

    if not text:
        raise ValueError("Empty LLM response")

    text = text.strip()

    # Remove markdown fences
    if "```" in text:
        parts = text.split("```")
        text = parts[-1].strip()

    # Find all possible JSON objects and try from the end
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

Fix this JSON to match the required schema EXACTLY.

RULES:
- Output ONLY JSON
- No markdown
- No explanation
- Must be valid JSON
- Must preserve intent

ERROR:
{error}

BROKEN JSON:
{bad_json_text}
"""

    response = client.chat.completions.create(
        model="qwen/qwen-2.5-coder-32b-instruct",
        messages=[
            {"role": "system", "content": "You repair invalid JSON structures."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )

    fixed = response.choices[0].message.content
    
    # 🔥 CRITICAL FIX
    return extract_json(fixed)