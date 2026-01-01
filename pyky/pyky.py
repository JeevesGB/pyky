import tkinter as tk
from tkinter import filedialog, messagebox
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
import math

# ================= CONFIG =================
SAMPLE_RATE = 22050
BUFFER_SIZE = 256
MAX_VOICES = 8

# ADSR (seconds)
ATTACK = 0.01
DECAY = 0.1
SUSTAIN = 0.6
RELEASE = 0.15

# ================= NOTES =================
BASE_NOTES = {
    "C": 261.63, "C#": 277.18,
    "D": 293.66, "D#": 311.13,
    "E": 329.63,
    "F": 349.23, "F#": 369.99,
    "G": 392.00, "G#": 415.30,
    "A": 440.00, "A#": 466.16,
    "B": 493.88
}

KEYMAP = {
    "z": "C", "s": "C#",
    "x": "D", "d": "D#",
    "c": "E",
    "v": "F", "g": "F#",
    "b": "G", "h": "G#",
    "n": "A", "j": "A#",
    "m": "B"
}

# ================= GLOBAL STATE =================
voices = []
octave = 0
duty_cycle = 0.5
recording = False
recorded_audio = []

# ================= VOICE =================
class Voice:
    def __init__(self, freq):
        self.freq = freq
        self.phase = 0.0
        self.time = 0.0
        self.releasing = False
        self.release_time = 0.0

    def envelope(self, dt):
        if not self.releasing:
            if self.time < ATTACK:
                return self.time / ATTACK
            elif self.time < ATTACK + DECAY:
                return 1 - (1 - SUSTAIN) * ((self.time - ATTACK) / DECAY)
            else:
                return SUSTAIN
        else:
            self.release_time += dt
            return max(0.0, SUSTAIN * (1 - self.release_time / RELEASE))

    def finished(self):
        return self.releasing and self.release_time >= RELEASE

# ================= AUDIO CALLBACK =================
def audio_callback(outdata, frames, time, status):
    global recorded_audio

    buffer = np.zeros(frames)
    dt = 1.0 / SAMPLE_RATE

    for v in voices[:]:
        for i in range(frames):
            phase = (v.phase * v.freq) % 1.0
            wave = 1.0 if phase < duty_cycle else -1.0
            env = v.envelope(dt)
            buffer[i] += wave * env
            v.phase += dt
            v.time += dt

        if v.finished():
            voices.remove(v)

    buffer /= max(1, MAX_VOICES)
    outdata[:, 0] = buffer

    if recording:
        recorded_audio.append(buffer.copy())

# ================= STREAM =================
stream = sd.OutputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    blocksize=BUFFER_SIZE,
    callback=audio_callback,
    dtype="float32",
    latency="low"
)
stream.start()

# ================= NOTE CONTROL =================
def note_on(note):
    if len(voices) >= MAX_VOICES:
        voices.pop(0)

    freq = BASE_NOTES[note] * (2 ** octave)
    voices.append(Voice(freq))

def note_off():
    for v in voices:
        v.releasing = True

# ================= RECORDING =================
def toggle_record(event=None):
    global recording, recorded_audio
    recording = not recording

    if recording:
        recorded_audio = []
        root.title("8-Bit Synth — RECORDING")
    else:
        root.title("8-Bit Synth")
        save_recording()

def save_recording():
    if not recorded_audio:
        messagebox.showwarning("No Recording", "Nothing recorded.")
        return

    data = np.concatenate(recorded_audio)

    file = filedialog.asksaveasfilename(
        defaultextension=".wav",
        filetypes=[("WAV", "*.wav")]
    )
    if not file:
        return

    write(file, SAMPLE_RATE, data)
    messagebox.showinfo("Saved", f"Saved:\n{file}")

# ================= UI =================
root = tk.Tk()
root.title("8-Bit Synth")

frame = tk.Frame(root)
frame.pack(pady=10)

white_keys = ["C", "D", "E", "F", "G", "A", "B"]
black_keys = ["C#", "D#", None, "F#", "G#", "A#", None]

for i, note in enumerate(white_keys):
    btn = tk.Button(frame, text=note, width=6, height=10)
    btn.grid(row=0, column=i, padx=1)
    btn.bind("<ButtonPress-1>", lambda e, n=note: note_on(n))
    btn.bind("<ButtonRelease-1>", lambda e: note_off())

for i, note in enumerate(black_keys):
    if note:
        btn = tk.Button(frame, text=note, width=4, height=6,
                        bg="black", fg="white")
        btn.place(x=40 + i * 60, y=0)
        btn.bind("<ButtonPress-1>", lambda e, n=note: note_on(n))
        btn.bind("<ButtonRelease-1>", lambda e: note_off())

# ================= CONTROLS =================
def octave_up():
    global octave
    octave = min(octave + 1, 3)

def octave_down():
    global octave
    octave = max(octave - 1, -3)

tk.Button(root, text="Octave −", command=octave_down).pack(side="left", padx=5)
tk.Button(root, text="Octave +", command=octave_up).pack(side="left", padx=5)

def set_duty(val):
    global duty_cycle
    duty_cycle = float(val)

tk.Scale(
    root,
    from_=0.1,
    to=0.9,
    resolution=0.05,
    orient="horizontal",
    label="Duty Cycle",
    command=set_duty
).pack(fill="x", padx=10)

# ================= KEYS =================
def key_press(e):
    if e.char.lower() in KEYMAP:
        note_on(KEYMAP[e.char.lower()])

def key_release(e):
    if e.char.lower() in KEYMAP:
        note_off()

root.bind("<KeyPress>", key_press)
root.bind("<KeyRelease>", key_release)
root.bind("<F1>", toggle_record)

tk.Label(
    root,
    text="Z–M keys | Hold notes | F1 = Record (WAV)",
    fg="gray"
).pack(pady=5)

root.mainloop()

stream.stop()
stream.close()
