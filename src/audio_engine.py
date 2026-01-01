import sounddevice as sd
import numpy as np

class AudioEngine:
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        self.voices = []
        self.recording = False
        self.recorded = []

    def callback(self, outdata, frames, time, status):
        dt = 1 / self.sample_rate
        buffer = np.zeros(frames)

        for i in range(frames):
            for v in self.voices:
                buffer[i] += v.sample(dt)

        buffer /= max(1, len(self.voices))
        outdata[:, 0] = buffer

        if self.recording:
            self.recorded.append(buffer.copy())

    def start(self):
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=1,
            callback=self.callback,
            dtype="float32",
            latency="low"
        )
        self.stream.start()
