def detect_intent(user_input: str, session: dict | None) -> str:
    if not session or not session.get("state"):
        return "NEW_PROMPT"
    return "EVOLVE_STATE"