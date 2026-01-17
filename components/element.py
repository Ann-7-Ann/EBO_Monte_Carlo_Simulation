class OpticalElement:
    def intersect(self, ray):
        raise NotImplementedError

    def interact(self, ray, hit):
        raise NotImplementedError

    def draw(self, screen):
        pass 
    
    def move(self, dx, dy):
        self.p1.x += dx
        self.p1.y += dy
        self.p2.x += dx
        self.p2.y += dy

    def get_params_str(self):
        raise NotImplementedError