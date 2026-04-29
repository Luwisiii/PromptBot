import json
from pathlib import Path
from jsonschema import validate

# Absolute path to this file → then go to schemas
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "schemas" / "media_schema.json"

with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    MEDIA_SCHEMA = json.load(f)


def validate_media_json(data: dict):
    validate(instance=data, schema=MEDIA_SCHEMA)