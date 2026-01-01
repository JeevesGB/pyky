class StepSequencer:
    def __init__(self, steps=16):
        self.steps = steps
        self.pattern = [[None for _ in range(steps)] for _ in range(12)]
        self.position = 0
        self.bpm = 120

    def tick(self):
        notes = []
        for row in range(12):
            note = self.pattern[row][self.position]
            if note:
                notes.append(note)
        self.position = (self.position + 1) % self.steps
        return notes
