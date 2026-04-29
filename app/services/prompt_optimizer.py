def optimize_image(prompt, style, extras):
    style_map = {
        "anime": "anime style, highly detailed, soft lighting, vibrant colors",
        "cinematic": "cinematic composition, film grain, depth of field, dramatic lighting",
        "realistic": "photorealistic, ultra-detailed, 8k, natural lighting",
        "cyberpunk": "cyberpunk aesthetic, neon lights, rainy atmosphere, futuristic city"
    }

    style_text = style_map.get(style or "", "")
    extras = extras or {}

    extras_text = ", ".join([f"{k}: {v}" for k, v in extras.items() if v])

    parts = [
        prompt or "",
        style_text,
        "ultra detailed",
        "high quality",
        "sharp focus",
        extras_text
    ]

    return ", ".join([p.strip() for p in parts if p and p.strip()])


def optimize_video(prompt, style, extras):
    extras = extras or {}

    parts = [
        prompt or "",
        "cinematic motion, smooth camera movement",
        style or "cinematic",
        "high temporal consistency, stable frames",
        f"camera: {extras.get('camera_motion', 'static')}",
        f"lighting: {extras.get('lighting', 'natural')}",
        "ultra realistic, film quality"
    ]

    return ", ".join([p.strip() for p in parts if p and p.strip()])


def optimize_audio(prompt, style, extras):
    extras = extras or {}

    parts = [
        prompt or "",
        "clear speech, studio quality audio",
        f"style: {style or 'neutral'}",
        f"voice: {extras.get('voice', 'natural')}",
        f"background: {extras.get('music', 'none')}",
        "high clarity, noise-free recording"
    ]

    return ", ".join([p.strip() for p in parts if p and p.strip()])


# ✅ FIX: ONLY ONE ENTRY POINT (IMPORTANT)
def optimize_prompt(compiled: dict) -> str:
    t = compiled.get("type")
    prompt = compiled.get("prompt", "")
    style = compiled.get("style")
    extras = compiled.get("extras", {})

    if t == "image":
        return optimize_image(prompt, style, extras)

    if t == "video":
        return optimize_video(prompt, style, extras)

    if t == "audio":
        return optimize_audio(prompt, style, extras)

    return prompt