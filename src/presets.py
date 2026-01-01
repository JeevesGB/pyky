import json

def save_preset(path, state):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)

def load_preset(path):
    with open(path) as f:
        return json.load(f)
