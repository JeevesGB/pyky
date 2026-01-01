import math
import random

class Voice:
    def __init__(self, freq, sample_rate=44100, adsr=None):
        self.freq = freq
        self.sample_rate = sample_rate
        self.phase = 0.0
        self.adsr = adsr or {"A":0.01,"D":0.1,"S":0.8,"R":0.2}

        # ADSR timers
        self.time = 0.0            # Attack/Decay/Sustain timer
        self.releasing = False
        self.release_time = 0.0    # Release timer
        self.release_start_amplitude = 0.0

    def envelope(self, dt):
        A = self.adsr["A"]
        D = self.adsr["D"]
        S = self.adsr["S"]
        R = self.adsr["R"]

        if self.releasing:
            self.release_time += dt
            if R == 0:
                return 0.0
            return max(0.0, self.release_start_amplitude * (1 - self.release_time / R))
        else:
            self.time += dt
            t = self.time
            if t < A:  # Attack
                return t / A
            elif t < A + D:  # Decay
                return 1 - (1 - S) * ((t - A)/D)
            else:  # Sustain
                return S

    def release(self):
        if not self.releasing:
            self.releasing = True
            self.release_time = 0.0
            self.release_start_amplitude = self.envelope(0)

    def sample(self, dt):
        amp = self.envelope(dt)
        return self._wave(dt) * amp

    def _wave(self, dt):
        return 0.0  # Override in subclasses

# ================= SUBCLASSES =================
class Pulse(Voice):
    def __init__(self, freq, duty=0.5, adsr=None):
        super().__init__(freq, adsr=adsr)
        self.duty = duty

    def _wave(self, dt):
        self.phase += self.freq * dt
        if self.phase >= 1:
            self.phase -= 1
        return 1.0 if self.phase < self.duty else -1.0

class Triangle(Voice):
    def _wave(self, dt):
        self.phase += self.freq * dt
        if self.phase >= 1:
            self.phase -= 1
        return 4.0 * abs(self.phase - 0.5) - 1.0

class Noise(Voice):
    def _wave(self, dt):
        return 2.0 * (random.random() - 0.5)
