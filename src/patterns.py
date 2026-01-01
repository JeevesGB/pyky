import json

def save_pattern(path, sequencer, meta=None):
    data = {
        "steps": sequencer.steps,
        "bpm": sequencer.bpm,
        "pattern": sequencer.pattern,
        "meta": meta or {}
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_pattern(path, sequencer):
    with open(path) as f:
        data = json.load(f)

    sequencer.steps = data["steps"]
    sequencer.bpm = data["bpm"]
    sequencer.pattern = data["pattern"]
