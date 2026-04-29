from typing import Dict, Tuple


# =========================
# MODEL PROFILES (Phase 9.5 core)
# =========================
MODEL_PROFILES = {
    "sdxl": {
        "visual": 0.95,
        "motion": 0.2,
        "audio": 0.0
    },
    "pika-labs": {
        "visual": 0.7,
        "motion": 0.95,
        "audio": 0.0
    },
    "elevenlabs-standard": {
        "visual": 0.0,
        "motion": 0.1,
        "audio": 0.95
    }
}


# =========================
# FEATURE DETECTOR (simple v1 heuristic)
# =========================
def detect_features(prompt: str) -> Dict[str, float]:
    prompt = (prompt or "").lower()

    visual_keywords = ["city", "light", "cinematic", "landscape", "sunset", "neon", "scene"]
    motion_keywords = ["camera", "motion", "moving", "tracking", "zoom", "pan"]
    audio_keywords = ["music", "sound", "voice", "audio", "piano", "beat"]

    def score(words):
        return sum(1 for w in words if w in prompt) / max(len(words), 1)

    return {
        "visual": score(visual_keywords),
        "motion": score(motion_keywords),
        "audio": score(audio_keywords)
    }


# =========================
# MODEL SCORING
# =========================
def score_model(features: Dict[str, float], model: str) -> float:
    profile = MODEL_PROFILES.get(model, {})

    score = (
        features["visual"] * profile.get("visual", 0) +
        features["motion"] * profile.get("motion", 0) +
        features["audio"] * profile.get("audio", 0)
    )

    return round(score, 3)


# =========================
# MAIN RANKER
# =========================
def rank_models(prompt: str) -> Dict:
    features = detect_features(prompt)

    scores = {
        model: score_model(features, model)
        for model in MODEL_PROFILES
    }

    ranking = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    best_model, best_score = ranking[0]

    return {
        "features": features,
        "scores": scores,
        "ranking": ranking,
        "best_model": best_model,
        "confidence": best_score
    }