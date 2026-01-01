import numpy as np
from scipy.io.wavfile import write
from voices import Pulse, Triangle, Noise

SAMPLE_RATE = 22050

def render_pattern(
    sequencer,
    wave="pulse",
    duty=0.5,
    octave=0,
    length_bars=1,
    filename="pattern.wav"
):
    step_time = 60 / sequencer.bpm / 4
    total_steps = sequencer.steps * length_bars
    samples_per_step = int(step_time * SAMPLE_RATE)

    output = []

    for step in range(total_steps):
        col = step % sequencer.steps

        step_buffer = np.zeros(samples_per_step)

        for row in range(len(sequencer.pattern)):
            if sequencer.pattern[row][col]:
                freq = 261.63 * (2 ** (row / 12)) * (2 ** octave)

                if wave == "pulse":
                    voice = Pulse(freq, duty)
                elif wave == "triangle":
                    voice = Triangle(freq)
                else:
                    voice = Noise()

                for i in range(samples_per_step):
                    step_buffer[i] += voice.sample(1 / SAMPLE_RATE)

        step_buffer /= max(1, len(sequencer.pattern))
        output.append(step_buffer)

    audio = np.concatenate(output)
    write(filename, SAMPLE_RATE, audio.astype("float32"))
