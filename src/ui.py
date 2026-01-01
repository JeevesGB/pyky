import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import time

from audio_engine import AudioEngine
from sequencer import StepSequencer
from voices import Pulse, Triangle, Noise
from patterns import save_pattern, load_pattern
from renderer import render_pattern

# ================= CONFIG =================
STEPS = 16
ROWS = 12
FONT = ("Consolas", 9)

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F",
              "F#", "G", "G#", "A", "A#", "B"]

BASE_FREQ = 261.63  # C4

# ================= HELPERS =================
def note_to_freq(note_index, octave):
    return BASE_FREQ * (2 ** (note_index / 12)) * (2 ** octave)

# ================= ENGINE =================
engine = AudioEngine()
engine.start()

sequencer = StepSequencer(STEPS)

# ================= UI ROOT =================
root = tk.Tk()
root.title("PyKY — NES Tracker")
root.configure(bg="#1e1e1e")

# ================= STATE =================
playing = False
cells = [[None for _ in range(STEPS)] for _ in range(ROWS)]

current_wave = tk.StringVar(value="pulse")
current_duty = tk.DoubleVar(value=0.5)
current_octave = tk.IntVar(value=0)

# ================= TOOLBAR =================
toolbar = tk.Frame(root, bg="#222")
toolbar.pack(fill="x")

def save_pattern_ui():
    path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("Pattern", "*.json")]
    )
    if path:
        save_pattern(path, sequencer)

def load_pattern_ui():
    path = filedialog.askopenfilename(
        filetypes=[("Pattern", "*.json")]
    )
    if path:
        load_pattern(path, sequencer)
        refresh_grid()

def export_wav_ui():
    path = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("WAV", "*.wav")]
    )
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

        engine.voices.clear()

        for r in range(ROWS):
            if sequencer.pattern[r][col]:
                freq = note_to_freq(r, current_octave.get())
                if current_wave.get() == "pulse":
                    engine.voices.append(Pulse(freq, current_duty.get()))
                elif current_wave.get() == "triangle":
                    engine.voices.append(Triangle(freq))
                else:
                    engine.voices.append(Noise())

        last_col = col
        time.sleep(step_time)

# ================= FOOTER =================
tk.Label(
    root,
    text="PyKY NES Tracker — Save patterns • Export WAV • Pulse / Triangle / Noise",
    fg="#777",
    bg="#1e1e1e"
).pack(pady=4)

root.mainloop()

engine.stream.stop()
engine.stream.close()
