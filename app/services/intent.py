EDIT_PATTERNS = [
    "change", "replace", "remove", "add", "make it",
    "instead", "not", "use", "turn", "modify",
    "more", "less", "increase", "decrease",
    "darker", "brighter", "zoom", "wider", "closer",
]


def looks_like_edit(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in EDIT_PATTERNS)

TRANSFORM_WORDS = [
    "turn into", "change to", "become", "make it a",
    "instead", "reimagine", "transform", "redesign"
]

def is_transform_edit(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in TRANSFORM_WORDS)

def detect_intent(user_input: str, session: dict | None) -> str:
    if not session or not session.get("last_prompt"):
        return "NEW_PROMPT"

    if is_transform_edit(user_input):
        return "TRANSFORM_PROMPT"

    if looks_like_edit(user_input):
        return "EDIT_PROMPT"

    return "NEW_PROMPT"