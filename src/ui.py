import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time

from audio_engine import AudioEngine
from sequencer import StepSequencer
from voices import Pulse, Triangle, Noise
from patterns import save_pattern, load_pattern
from renderer import render_pattern

# Optional MIDI
try:
    import mido
    midi_available = True
except ImportError:
    midi_available = False

# ================= CONFIG =================
STEPS = 16
ROWS = 12
FONT = ("Consolas", 9)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

BASE_FREQ = 261.63  # C4

KEYBOARD_NOTES = [
    "C3","C#3","D3","D#3","E3","F3","F#3","G3","G#3","A3","A#3","B3",
    "C4","C#4","D4","D#4","E4","F4","F#4","G4","G#4","A4","A#4","B4","C5"
]

KEYBOARD_KEYS = [
    "z","s","x","d","c","v","g","b","h","n","j","m",
    "q","2","w","3","e","r","5","t","6","y","7","u","i"
]

# ================= HELPERS =================
def note_to_freq_name(note_name):
    if len(note_name) == 3:
        note = note_name[:2]
        octave = int(note_name[2])
    else:
        note = note_name[0]
        octave = int(note_name[1])
    semitone = NOTE_NAMES.index(note)
    return BASE_FREQ * (2 ** (semitone / 12)) * (2 ** (octave - 4))

# ================= ENGINE =================
engine = AudioEngine()
engine.start()

sequencer = StepSequencer(STEPS)

# ================= UI ROOT =================
root = tk.Tk()
root.title("PyKY — NES Tracker + Keyboard")
root.configure(bg="#1e1e1e")

# ================= STATE =================
playing = False
cells = [[None for _ in range(STEPS)] for _ in range(ROWS)]
active_notes = {}  # Tracks currently held notes

current_wave = tk.StringVar(value="pulse")
current_duty = tk.DoubleVar(value=0.5)
current_octave = tk.IntVar(value=0)
live_mode = tk.BooleanVar(value=True)

# ================= TOOLBAR =================
toolbar = tk.Frame(root, bg="#222")
toolbar.pack(fill="x")

def save_pattern_ui():
    path = filedialog.asksaveasfilename(defaultextension=".json")
    if path:
        save_pattern(path, sequencer)

def load_pattern_ui():
    path = filedialog.askopenfilename()
    if path:
        load_pattern(path, sequencer)
        refresh_grid()

def export_wav_ui():
    path = filedialog.asksaveasfilename(defaultextension=".wav")
    if path:
        render_pattern(
            sequencer,
            wave=current_wave.get(),
            duty=current_duty.get(),
            octave=current_octave.get(),
            filename=path
        )
        messagebox.showinfo("Exported", f"WAV exported:\n{path}")

tk.Button(toolbar, text="Save Pattern", command=save_pattern_ui).pack(side="left", padx=4)
tk.Button(toolbar, text="Load Pattern", command=load_pattern_ui).pack(side="left", padx=4)
tk.Button(toolbar, text="Export WAV", command=export_wav_ui).pack(side="left", padx=4)
tk.Checkbutton(toolbar, text="Live Mode", variable=live_mode, bg="#222", fg="#ccc").pack(side="right", padx=4)

# ================= MAIN FRAME =================
main = tk.Frame(root, bg="#1e1e1e")
main.pack(padx=10, pady=10)

# ================= TRACKER GRID =================
grid = tk.Frame(main, bg="#1e1e1e")
grid.pack()

def toggle_cell(r, c):
    if sequencer.pattern[r][c]:
        sequencer.pattern[r][c] = None
        cells[r][c].config(bg="#111")
    else:
        sequencer.pattern[r][c] = True
        cells[r][c].config(bg="#2ecc71")

def refresh_grid():
    for r in range(ROWS):
        for c in range(STEPS):
            cells[r][c].config(
                bg="#2ecc71" if sequencer.pattern[r][c] else "#111"
            )

# Column headers
for c in range(STEPS):
    tk.Label(
        grid,
        text=f"{c:02}",
        fg="#888",
        bg="#1e1e1e",
        font=FONT
    ).grid(row=0, column=c + 1)

# Rows + cells
for r in range(ROWS):
    tk.Label(
        grid,
        text=NOTE_NAMES[r],
        fg="#ccc",
        bg="#1e1e1e",
        font=FONT
    ).grid(row=ROWS - r, column=0)

    for c in range(STEPS):
        b = tk.Button(
            grid,
            width=2,
            height=1,
            bg="#111",
            activebackground="#2ecc71",
            relief="flat",
            command=lambda r=r, c=c: toggle_cell(r, c)
        )
        b.grid(row=ROWS - r, column=c + 1, padx=1, pady=1)
        cells[r][c] = b

# ================= CONTROLS =================
controls = tk.Frame(main, bg="#1e1e1e")
controls.pack(pady=6)

tk.Label(controls, text="Wave", fg="#ccc", bg="#1e1e1e").grid(row=0, column=0)
tk.OptionMenu(
    controls,
    current_wave,
    "pulse", "triangle", "noise"
).grid(row=0, column=1)

tk.Label(controls, text="Duty", fg="#ccc", bg="#1e1e1e").grid(row=1, column=0)
tk.Scale(
    controls,
    from_=0.125,
    to=0.75,
    resolution=0.125,
    orient="horizontal",
    variable=current_duty,
    bg="#1e1e1e",
    fg="#ccc",
    highlightthickness=0
).grid(row=1, column=1)

tk.Label(controls, text="Octave", fg="#ccc", bg="#1e1e1e").grid(row=2, column=0)
tk.Spinbox(
    controls,
    from_=-3,
    to=3,
    width=5,
    textvariable=current_octave
).grid(row=2, column=1)

# ================= TRANSPORT =================
transport = tk.Frame(main, bg="#1e1e1e")
transport.pack(pady=6)

def play():
    global playing
    if playing:
        return
    playing = True
    threading.Thread(target=sequencer_loop, daemon=True).start()

def stop():
    global playing
    playing = False
    engine.voices.clear()
    active_notes.clear()

tk.Button(transport, text="Play", command=play).pack(side="left", padx=5)
tk.Button(transport, text="Stop", command=stop).pack(side="left", padx=5)

# ================= SEQUENCER LOOP =================
def sequencer_loop():
    global playing
    step_time = 60 / sequencer.bpm / 4
    last_col = -1

    while playing:
        col = sequencer.position
        sequencer.tick()

        # Clear previous highlight
        if last_col >= 0:
            for r in range(ROWS):
                cells[r][last_col].config(
                    bg="#2ecc71" if sequencer.pattern[r][last_col] else "#111"
                )

        # Highlight current column
        for r in range(ROWS):
            cells[r][col].config(bg="#444")

        # Play tracker notes if live mode is OFF
        if not live_mode.get():
            engine.voices.clear()
            for r in range(ROWS):
                if sequencer.pattern[r][col]:
                    freq = note_to_freq_name(NOTE_NAMES[r] + str(current_octave.get() + 4))
                    if current_wave.get() == "pulse":
                        engine.voices.append(Pulse(freq, current_duty.get()))
                    elif current_wave.get() == "triangle":
                        engine.voices.append(Triangle(freq))
                    else:
                        engine.voices.append(Noise())

        last_col = col
        time.sleep(step_time)

# ================= 25-KEY SYNTH KEYBOARD =================
keyboard_frame = tk.Frame(root, bg="#1e1e1e")
keyboard_frame.pack(pady=6)

key_buttons = []

def press_key(note_name):
    if note_name in active_notes:
        return
    freq = note_to_freq_name(note_name)
    if current_wave.get() == "pulse":
        voice = Pulse(freq, current_duty.get())
    elif current_wave.get() == "triangle":
        voice = Triangle(freq)
    else:
        voice = Noise()
    active_notes[note_name] = voice
    engine.voices.append(voice)

def release_key(note_name):
    if note_name in active_notes:
        voice = active_notes.pop(note_name)
        if voice in engine.voices:
            engine.voices.remove(voice)

# On-screen keyboard buttons
for i, note in enumerate(KEYBOARD_NOTES):
    color = "white" if "#" not in note else "black"
    fg = "black" if color == "white" else "white"
    b = tk.Button(
        keyboard_frame,
        text=note,
        bg=color,
        fg=fg,
        width=3,
        height=8,
        relief="raised"
    )
    b.grid(row=0, column=i, padx=1, pady=1)
    b.bind("<ButtonPress-1>", lambda e, n=note: press_key(n))
    b.bind("<ButtonRelease-1>", lambda e, n=note: release_key(n))
    key_buttons.append(b)

# ================= KEYBOARD SHORTCUTS =================
def key_press(event):
    if event.char in KEYBOARD_KEYS:
        index = KEYBOARD_KEYS.index(event.char)
        press_key(KEYBOARD_NOTES[index])

def key_release(event):
    if event.char in KEYBOARD_KEYS:
        index = KEYBOARD_KEYS.index(event.char)
        release_key(KEYBOARD_NOTES[index])

root.bind("<KeyPress>", key_press)
root.bind("<KeyRelease>", key_release)

# ================= FOOTER =================
tk.Label(
    root,
    text="PyKY NES Tracker + 25-Key Keyboard — Save patterns • Export WAV • Pulse/Triangle/Noise",
    fg="#777",
    bg="#1e1e1e"
).pack(pady=4)

# ================= MIDI INPUT THREAD =================
def midi_listener():
    if not midi_available:
        return
    try:
        with mido.open_input() as port:
            for msg in port:
                if not live_mode.get():
                    continue
                if msg.type == "note_on" and msg.velocity > 0:
                    freq = 261.63 * (2 ** ((msg.note - 69) / 12))
                    note_name = f"midi{msg.note}"
                    if note_name not in active_notes:
                        if current_wave.get() == "pulse":
                            voice = Pulse(freq, current_duty.get())
                        elif current_wave.get() == "triangle":
                            voice = Triangle(freq)
                        else:
                            voice = Noise()
                        active_notes[note_name] = voice
                        engine.voices.append(voice)
                elif msg.type in ("note_off", "note_on"):
                    note_name = f"midi{msg.note}"
                    if note_name in active_notes:
                        voice = active_notes.pop(note_name)
                        if voice in engine.voices:
                            engine.voices.remove(voice)
    except:
        pass

if midi_available:
    threading.Thread(target=midi_listener, daemon=True).start()

root.mainloop()

engine.stream.stop()
engine.stream.close()
