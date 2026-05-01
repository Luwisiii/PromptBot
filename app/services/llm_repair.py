import json
from json import JSONDecodeError
from app.llm_client import get_client


def extract_json(text: str) -> dict:
    """
    Safely extract first JSON object from LLM text.
    No regex. No LLM repair.
    """

    if not text:
        raise ValueError("Empty LLM response")

    text = text.strip()

    # Remove markdown fences
    if "```" in text:
        parts = text.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("{"):
                text = p
                break

    # Direct parse
    try:
        return json.loads(text)
    except JSONDecodeError:
        pass

    # Fallback: find first {...}
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError(f"No JSON found:\n{text}")

    candidate = text[start:end + 1]
    return json.loads(candidate)

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
        model="deepseek/deepseek-chat",
        messages=[
            {"role": "system", "content": "You repair invalid JSON structures."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
    )
    
    return json.loads(response.choices[0].message.content)