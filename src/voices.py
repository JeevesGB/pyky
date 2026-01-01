import math

class Voice:
    def __init__(self, freq, sample_rate=44100, adsr=None):
        self.freq = freq
        self.sample_rate = sample_rate
        self.phase = 0
        self.adsr = adsr or {"A":0.01,"D":0.1,"S":0.8,"R":0.2}
        self.time = 0
        self.releasing = False
        self.release_start_amplitude = 1.0

    def envelope(self, dt):
        A = self.adsr["A"]
        D = self.adsr["D"]
        S = self.adsr["S"]
        R = self.adsr["R"]

        t = self.time

        if self.releasing:
            return max(0, self.release_start_amplitude * (1 - (t / R)))
        else:
            if t < A:
                return t / A
            elif t < A + D:
                return 1 - (1 - S) * ((t - A)/D)
            else:
                return S

    def release(self):
        self.releasing = True
        self.time = 0
        self.release_start_amplitude = self.envelope(0)

    def sample(self, dt):
        self.time += dt
        amp = self.envelope(dt)
        return self._wave(dt) * amp

    def _wave(self, dt):
        # override in Pulse / Triangle / Noise
        return 0

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
        return 4 * abs(self.phase - 0.5) - 1

class Noise(Voice):
    import random
    def _wave(self, dt):
        return 2 * (self.random.random() - 0.5)
