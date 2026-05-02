EDIT_WORDS = [
    "change", "replace", "remove", "add", "make it",
    "instead", "not", "use", "turn", "modify"
]


def looks_like_edit(text: str) -> bool:
    t = text.lower()
    return any(w in t for w in EDIT_WORDS)


def detect_intent(user_input: str, session: dict | None) -> str:
    """
    Returns:
    - NEW_PROMPT
    - EDIT_PROMPT
    - OUT_OF_SCOPE
    """
    
    if session and session.get("last_prompt"):
        if looks_like_edit(user_input):
            return "EDIT_PROMPT"
        return "NEW_PROMPT"

    return "NEW_PROMPT"