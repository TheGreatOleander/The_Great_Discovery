
class PressureField:

    def __init__(self):
        self.semantic = 0
        self.topology = 0
        self.cross_domain = 0
        self.resonance = 0

    def total(self):
        return (
            self.semantic +
            self.topology +
            self.cross_domain +
            self.resonance
        )
