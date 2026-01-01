import mido

def listen(engine, note_to_freq):
    with mido.open_input() as port:
        for msg in port:
            if msg.type == "note_on" and msg.velocity > 0:
                engine.voices.append(note_to_freq(msg.note))
            elif msg.type in ("note_off", "note_on"):
                engine.voices.clear()
