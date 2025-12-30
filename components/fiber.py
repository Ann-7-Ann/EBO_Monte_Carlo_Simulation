from core.matrices import free_space
from .element import OpticalElement

class Fiber(OpticalElement):
    def __init__(self, x, length, n):
        super().__init__(x)
        self.length = length
        self.n = n

    def matrix(self):
        return free_space(self.length / self.n)
