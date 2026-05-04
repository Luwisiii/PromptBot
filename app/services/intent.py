EDIT_PATTERNS = [
    "change", "replace", "remove", "add", "make it",
    "instead", "not", "use", "turn", "modify",
    "more", "less", "increase", "decrease",
    "darker", "brighter", "zoom", "wider", "closer",
]


def looks_like_edit(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in EDIT_PATTERNS)


def detect_intent(user_input: str, session: dict | None) -> str:
    if session and session.get("last_prompt") and looks_like_edit(user_input):
        return "EDIT_PROMPT"
    return "NEW_PROMPT"