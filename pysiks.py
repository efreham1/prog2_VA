import numpy as np

class Object:

    def __init__(self, m, x, y, vx, vy) -> None:
        self.pos = np.array([float(x), float(y)])
        self.vel = np.array([float(vx), float(vy)])
        self.acc = np.zeros(2)
        self.mass = m
    
    def update(self, dt, *forces):
        F = np.zeros(2)
        for f in forces:
            F += f.get()
        self.acc = F/self.mass
        self.pos += self.vel*float(dt) + self.acc*float(dt)**2/2
        self.vel += self.acc*float(dt)
        
    

    def move_to(self, x, y):
        self.pos = np.array([float(x), float(y)])
    
    def get_pos(self):
        return self.pos
    
    def get_vel(self):
        return self.vel
    
    def get_acc(self):
        return self.acc

class Force:

    def __init__(self, x, y, t = 0) -> None:
        self.F = np.array([float(x), float(y)])
        self.time = float(t)

    def update_t(self, dt):
        self.time -= float(dt)
        if self.time < 0:
            self.F = np.zeros(2)
    
    def set_F(self, x, y):
        self.F = np.array([float(x), float(y)])
    
    def get(self):
        return self.F
        
