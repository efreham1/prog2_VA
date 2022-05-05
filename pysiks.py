from matplotlib.patches import Rectangle
import numpy as np
import concurrent.futures as future

class Physics_Canvas:
    
    def __init__(self, w, h, res) -> None:
        if w%2 == 1 or h%2 == 1:
            raise Exception('Uneven width and/or height is unsupported')
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
            self.cal_corners()
            self.moveable = True
        
        def cal_corners(self):
            r = np.sqrt((self.width**2+self.height**2)/4)
            a = np.arctan(self.height/self.width)
            self.corners = [
                np.array([r*np.cos(a+self.angle), r*np.sin(a+self.angle)])+self.pos,
                np.array([r*np.cos(np.pi-a+self.angle), r*np.sin(np.pi-a+self.angle)])+self.pos,
                np.array([r*np.cos(np.pi+a+self.angle), r*np.sin(np.pi+a+self.angle)])+self.pos,
                np.array([r*np.cos(2*np.pi-a+self.angle), r*np.sin(2*np.pi-a+self.angle)])+self.pos
                ] #start at top right goes anti-clockwise

        def proj_dir(self):
            dir1 = self.corners[1]-self.corners[0]
            e1 = dir1/np.linalg.norm(dir1)
            dir2 = self.corners[0]-self.corners[3]
            e2 = dir2/np.linalg.norm(dir2)
            return e1, e2

        def move_to(self, p):
            self.pos = p.astype(np.float64)
            self.cal_corners()
        
        def rotate_to(self, theta):
            self.angle = float(theta)
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
                self.cal_corners()
            else:
                pass
        
        def set_vel(self, v):
            self.vel = v.astype(np.float64)
        
        def creep(self, d, s):
            self.pos += s*d.astype(np.float64)
            self.cal_corners()
    
    def point_on_line(self, p1, p2, p3): # closest point on line p1-p2 to p3
        x1, y1 = p1[0], p1[1]
        x2, y2 = p2[0], p2[1]
        x3, y3 = p3[0], p3[1]
        dx, dy = x2-x1, y2-y1
        det = dx**2 + dy**2
        a = (dy*(y3-y1)+dx*(x3-x1))/det #solving the equations system for the two lines' intersection, 2nd line being p3 and along the normal to p1-p2
        return np.array([x1+a*dx, y1+a*dy])

    def force_a_cal(self, rects, old_vs, dt):
        dp1 = -2*rects[1].mass/(rects[0].mass + rects[1].mass)*np.dot(old_vs[0]-old_vs[1], rects[0].pos-rects[1].pos)/(np.linalg.norm(rects[0].pos-rects[1].pos)**2)*(rects[0].pos-rects[1].pos)*rects[0].mass
        dp2 = -2*rects[0].mass/(rects[1].mass + rects[0].mass)*np.dot(old_vs[1]-old_vs[0], rects[1].pos-rects[0].pos)/(np.linalg.norm(rects[1].pos-rects[0].pos)**2)*(rects[1].pos-rects[0].pos)*rects[1].mass
        F1 = dp1/dt
        F2 = dp2/dt
        point_of_force = rects[0].pos-(rects[0].pos-rects[1].pos)/2
        point_on_rect = [None, None]
        for n, rect in enumerate(rects):
            point_on_rect[n] = self.point_on_line(rect.corners[0], rect.corners[1], point_of_force)
            for i in range(1, 4):
                x = self.point_on_line(rect.corners[i], rect.corners[(i+1)%4], point_of_force)
                if np.linalg.norm(x-point_of_force)<np.linalg.norm(point_on_rect[n]-point_of_force):
                    point_on_rect[n] = x
        a1 = point_on_rect[0]-rects[0].pos
        a2 = point_on_rect[1]-rects[1].pos
        return F1, F2, a1, a2

    def collison_check(self, rects):
        rect1:Rectangle = rects[0]
        rect2:Rectangle = rects[1]
        e1, e2 = rect1.proj_dir()
        dir = [e1, e2]
        if rect1.angle%(np.pi/2) != rect2.angle%(np.pi/2):
            e3, e4 = rect2.proj_dir()
            dir.append(e3)
            dir.append(e4)
        coll = []
        for direction in dir:
            minmax = [[None,None], [None,None]]
            for i, rect in enumerate([rect1, rect2]):
                for corner in rect.corners:
                    x = np.dot(corner, direction)
                    if minmax[i][1] is None or x > minmax[i][1]:
                        minmax[i][1] = x
                    if minmax[i][0] is None or x < minmax[i][0]:
                        minmax[i][0] = x
            if minmax[0][0]>minmax[1][1] or minmax[1][0]>minmax[0][1]:
                coll.append(0)
            else:
                coll.append(1)
        if not 0 in coll:
            return rects


    def collision_detector(self, rects):
        rect_pairs = [[rect1, rect2] for rect1 in rects for rect2 in rects if np.linalg.norm(rect1.pos) < np.linalg.norm(rect2.pos)]
        colliding = []
        with future.ThreadPoolExecutor() as ex:
            results = ex.map(self.collison_check, rect_pairs)
            for r in results:
                if not r is None:
                    colliding.append(r)
        return colliding
        
        


    def collision_handler(self, rects, vs, dt):
        e1 = -vs[0]/np.linalg.norm(vs[0]) if np.any(vs[0]!= np.zeros(2)) else np.zeros(2)
        e2 = -vs[1]/np.linalg.norm(vs[1]) if np.any(vs[1]!= np.zeros(2)) else np.zeros(2)
        coll = self.collision_detector(rects)
        while not coll == []:
            rects[0].creep(e1, 1/self.res)
            rects[1].creep(e2, 1/self.res)
            coll = self.collision_detector(rects)
        
        F1, F2, a1, a2 = self.force_a_cal(rects, vs, dt)
        self.forces[self.rects.index(rects[0])]['Coll_F'] = [F1, dt, a1]
        self.forces[self.rects.index(rects[1])]['Coll_F'] = [F2, dt, a2]
        
        


    def collisions(self, old_vs, dt):
        collisions = self.collision_detector(self.rects)
        if not collisions is []:
            for pair in collisions:
                self.collision_handler(pair, [old_vs[pair[0]], old_vs[pair[1]]], dt)


    def update(self, dt):
        old_v = {}
        for i, rect in enumerate(self.rects):
            a = np.zeros(2)
            alpha = 0
            Dt = dt
            for name, force in self.forces[i].items():
                if force[1] == 'inf':
                    a += force[0]/rect.mass
                    alpha += np.linalg.norm(np.cross(force[2], force[0]))/rect.momI
                elif force[1]<= dt:
                    a += force[0]/rect.mass
                    alpha += np.linalg.norm(np.cross(force[2], force[0]))/rect.momI
                    Dt = force[1]
                    if Dt < 0:
                        raise Exception('Negative time differance')
                    self.forces[i][name] = 0
                else:
                    a += force[0]/rect.mass
                    alpha += np.linalg.norm(np.cross(force[2], force[0]))/rect.momI
                    force[1] += -dt
            self.forces[i] = {k: v for k, v in self.forces[i].items() if v != 0}
            
            s = a/2*Dt**2
            theta = alpha/2*Dt**2
            rect.move(dt, s)
            rect.rotate(dt, theta)
            old_v[rect] = np.copy(rect.vel)
            rect.vel += a*Dt
            rect.angle_vel += alpha*Dt

        self.collisions(old_v, dt)
    
    def gen_rect(self, name, w, h, m):
        if w==0 or h==0 or m==0:
            raise Exception("Width, height, or mass can't be zero")
        self.rects.append(self.Rectangle(w, h, m))
        i = len(self.rects)-1
        self.rect_names[name] = i
        self.forces[i] = {}

    def force(self, F, t, a, Fname, *names):
        for name in names:
            try:
                self.forces[self.rect_names[name]][Fname] = [F, t, a]
            except KeyError:
                raise Exception(f'There is no rectangle by the name {name}')


    def place_rect(self, name, x, y):
        try:
            self.rects[self.rect_names[name]].move_to(np.array([x, y]))
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')

    
    def rotate_rect(self, name, theta):
        try:
            self.rects[self.rect_names[name]].rotate_to(theta)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')
    
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
    
    def set_vel(self, name, vx, vy):
        self.rects[self.rect_names[name]].set_vel(np.array([vx, vy]))


    

e = Physics_Canvas(16, 16, 1000)

e.gen_rect('Tony', 1, 1, 2)
e.gen_rect('Bony', 1, 1, 1)
e.place_rect('Tony', 10, 0.4)
e.rotate_rect('Tony', np.pi/4)
e.set_vel('Tony', -1, 0)
print(f"Tony: {e.get_pos('Tony')}, {e.get_angle('Tony')}\nBony:{e.get_pos('Bony')}, {e.get_angle('Bony')}")
for _ in range(100):
    e.update(0.1)
    print(f"Tony: {e.get_pos('Tony')}, {e.get_angle('Tony')}\nBony:{e.get_pos('Bony')}, {e.get_angle('Bony')}")