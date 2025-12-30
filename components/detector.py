from components.element import OpticalElement
from simulation.hittest import point_segment_distance

class Detector(OpticalElement):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
        self.hits = []

    def intersect(self, ray):
        from simulation.intersection import ray_segment
        return ray_segment(ray, self.p1, self.p2)

    def interact(self, ray, hit):
        self.hits.append(hit)

    def contains_point(self, pos):
        return point_segment_distance(pos, self.p1, self.p2) < 8
