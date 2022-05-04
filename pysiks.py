from aifc import Error
import numpy as np
import concurrent.futures as future

class Physics_Canvas:
    
    def __init__(self, w, h, res) -> None:
        if w%2 == 1 or h%2 == 1:
            raise Error('Uneven width and/or height is unsupported')
        self.width = w
        self.height = h
        self.res = res
        self.rect_names = {}
        self.rects = []
        self.forces = {}


    class Rectangle:

        def __init__(self, w, h, m):
            self.width = w
            self.height = h
            self.mass = m
            self.momI = 1/12*3*(w**2+h**2)
            self.pos = np.zeros(2)
            self.vel = np.zeros(2)
            self.angle = 0
            self.angle_vel = 0
            self.corners = self.cal_corners()
            self.moveable = True
        
        def cal_corners(self):
            r = (self.width**2+self.height**2)/4
            a = np.tan(self.height/self.width)
            self.corners = [
                r*np.array([np.cos(a+self.angle), np.sin(a+self.angle)])+self.pos,
                r*np.array([np.cos(np.pi-a+self.angle), np.sin(np.pi-a+self.angle)])+self.pos,
                r*np.array([np.cos(np.pi+a+self.angle), np.sin(np.pi+a+self.angle)])+self.pos,
                r*np.array([np.cos(2*np.pi-a+self.angle), np.sin(2*np.pi-a+self.angle)])+self.pos
                ] #start at top right goes anti-clockwise

        def proj_dir(self):
            dir1 = self.corners[1]-self.corners[0]
            e1 = dir1/np.linalg.norm(dir1)
            dir2 = self.corners[0]-self.corners[3]
            e2 = dir2/np.linalg.norm(dir2)
            return e1, e2

        def move_to(self, x, y):
            self.pos = np.array([x,y])
            self.cal_corners()
        
        def rotate_to(self, theta):
            self.angle = theta
            self.cal_corners()
        
        def move(self, dt, s):
            if self.moveable:
                self.pos += self.vel*dt + s
                self.cal_corners()
            else:
                pass

        def rotate(self, dt, theta):
            if self.moveable:
                self.angle += self.angle_vel*dt + theta
                self.corners = self.cal_corners()
            else:
                pass
        
    
    def collison_detector(self, rects):
        pass

    def collision_detector_start(self, rects):
        rect_pairs = [[rect1, rect2] for rect1 in rects for rect2 in rects if rect1 < rect2]
        colliding = []
        with future.ProcessPoolExecutor() as ex:
            results = ex.map(self.collison_detector, rect_pairs)
            for r in results:
                colliding.append(r)
        return colliding
        
        


    def collision_handler(self, old_vs):
        pass

    def collisions(self):
        pass

    def update(self, dt):
        old_v = []
        for i, rect in enumerate(self.rects):
            a = np.zeros(2)
            alpha = 0
            Dt = dt
            for name, force in self.forces[i].items():
                if force[1] == 'inf':
                    a += force[0]/rect.mass
                    alpha += np.linalg.norm(force[0])*force[2]/rect.momI
                elif force[1]<= dt:
                    a += force[0]/rect.mass
                    alpha += np.linalg.norm(force[0])*force[2]/rect.momI
                    Dt = force[1]
                    if Dt < 0:
                        raise Error('Negative time differance')
                    self.forces[i][name] = 0
                else:
                    a += force[0]/rect.mass
                    alpha += np.linalg.norm(force[0])*force[2]/rect.momI
                    force[1] += -dt
            self.forces[i] = {k: v for k, v in self.forces[i].items() if v != 0}    
            
            s = a/2*Dt**2
            theta = alpha/2*Dt**2
            rect.move(dt, s)
            rect.rotate(dt, theta)
            old_v.append(rect.vel)
            rect.vel += a*Dt
            rect.angle_vel += alpha*Dt

        self.collisions()
    
    def gen_rect(self, name, w, h, m):
        self.rects.append(self.Rectangle(w, h, m))
        i = len(self.rects)-1
        self.rect_names[name] = i
        self.forces[i] = {}

    def force(self, F, t, a, Fname, *names):
        for name in names:
            try:
                self.forces[self.rect_names[name]][Fname] = [F, t, a]
            except KeyError:
                raise Error(f'There is no rectangle by the name {name}')


    def place_rect(self, name, x, y):
        try:
            self.rects[self.rect_names[name]].move_to(x,y)
        except KeyError:
            raise Error(f'There is no rectangle by the name {name}')

    
    def rotate_rect(self, name, theta):
        try:
            self.rects[self.rect_names[name]].rotate_to(theta)
        except KeyError:
            raise Error(f'There is no rectangle by the name {name}')
    
    def get_vel(self, name):
        return self.rects[self.rect_names[name]].vel
    
    def get_pos(self, name):
        return self.rects[self.rect_names[name]].pos
    
    def get_angle(self, name):
        return self.rects[self.rect_names[name]].angle

    def get_angle_vel(self, name):
        return self.rects[self.rect_names[name]].angle_vel

    def make_immoveable(self, name):
        self.rects[self.rect_names[name]].moveable = False
    
    def make_moveable(self, name):
        self.rects[self.rect_names[name]].moveable = True


    

e = Physics_Canvas(16, 16, 1000)

e.gen_rect('Tony', 1, 1, 2)
e.gen_rect('Bony', 1, 1, 1)
e.force(1, 1.5, 1, 'Acc', 'Tony')
e.force(2, 1.5, 1, 'Acc', 'Bony')
e.update(1)
print(e.get_pos('Tony'), e.get_pos('Bony'))
