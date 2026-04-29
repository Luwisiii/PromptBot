def route_model(compiled: dict) -> dict:
    """
    Converts generic structured prompt → model-specific execution plan
    """

    media_type = compiled.get("type")
    style = compiled.get("style", "")
    quality = compiled.get("quality", {})
    extras = compiled.get("extras", {})

    # -------------------------
    # IMAGE ROUTING
    # -------------------------
    if media_type == "image":

        # Simple heuristic routing
        if "realistic" in style or quality.get("steps", 0) > 40:
            model = "sdxl"
        elif "anime" in style:
            model = "sdxl-anime"
        elif "cinematic" in style:
            model = "sdxl-cinematic"
        else:
            model = "sdxl"

        return {
            **compiled,
            "model_target": model,
            "model_config": {
                "sampler": extras.get("sampler", "euler_a"),
                "cfg_scale": quality.get("guidance", 7.5),
                "steps": quality.get("steps", 30),
                "size": compiled["media"].get("resolution", "1024x1024")
            }
        }

    # -------------------------
    # VIDEO ROUTING
    # -------------------------
    if media_type == "video":

        camera = quality.get("camera_motion", "static")

        if quality.get("motion_strength", 0) > 0.7:
            model = "runway-gen2"
        else:
            model = "pika-labs"

        return {
            **compiled,
            "model_target": model,
            "model_config": {
                "fps": compiled["media"].get("fps", 24),
                "duration": compiled["media"].get("duration", 8),
                "camera_motion": camera
            }
        }

    # -------------------------
    # AUDIO ROUTING
    # -------------------------
    if media_type == "audio":

        voice_clarity = quality.get("voice_clarity", 0.5)

        if voice_clarity > 0.8:
            model = "elevenlabs-premium"
        else:
            model = "elevenlabs-standard"

        return {
            **compiled,
            "model_target": model,
            "model_config": {
                "sample_rate": compiled["media"].get("sample_rate", 44100),
                "format": compiled["media"].get("format", "mp3")
            }
        }

    # fallback
    return {
        **compiled,
        "model_target": "unknown"
    }