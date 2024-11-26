import json

def load_settings():
    with open("config/settings.json") as f:
        return json.load(f)

settings = load_settings()
