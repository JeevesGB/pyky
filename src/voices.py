import numpy as np
import random

class Pulse:
    def __init__(self, freq, duty):
        self.freq = freq
        self.phase = 0.0
        self.duty = duty
        self.env = 1.0

    def sample(self, dt):
        self.phase = (self.phase + self.freq * dt) % 1.0
        return 1.0 if self.phase < self.duty else -1.0

class Triangle:
    def __init__(self, freq):
        self.freq = freq
        self.phase = 0.0

    def sample(self, dt):
        self.phase = (self.phase + self.freq * dt) % 1.0
        return 2 * abs(2 * self.phase - 1) - 1

class Noise:
    def sample(self, dt):
        return random.uniform(-1, 1)
