from matplotlib.patches import Rectangle
import numpy as np
import concurrent.futures as future

class Physics_Canvas:
    
    def __init__(self, res) -> None:
        self.__res = res
        self.__rects = {}
        self.__notification = {}
        self.__surfaces = {}

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
            self.destructable = False
            self.forces = {}
        
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
        
        def move(self, dt, s, res):
            if self.moveable:
                ds = self.vel*dt + s
                if np.linalg.norm(ds) > 1/res:
                    self.pos += ds
                    self.cal_corners()
            else:
                return 'Tried moving, rectangle immoveable'

        def rotate(self, dt, theta, res):
            if self.moveable:
                da = self.angle_vel*dt + theta
                if da > np.pi*2/res:
                    self.angle += da
                    self.cal_corners()
            else:
                return 'Tried rotating, rectangle immoveable'
        
        def set_vel(self, v):
            self.vel = v.astype(np.float64)
        
        def creep(self, d, s):
            self.pos += s*d.astype(np.float64)
            self.cal_corners()
        
        def moveability(self, bool):
            self.moveable = bool
        
        def destructability(self, bool):
            self.destructable = bool
    
    class Surface:

        def __init__(self, coeff_fric, xrange, yrange, g, air, Rects):
            self.coeff_of_friction = coeff_fric
            self.x_range = xrange
            self.y_range = yrange
            self.message = ''
            self.to_Notify = False
            self.g = g
            self.for_rects = Rects
            self.air = air

        def on_surface(self, rect):
            return self.x_range[0]<=rect.pos[0]<self.x_range[1] and self.y_range[0]<=rect.pos[1]<self.y_range[1]
        
        def add_notify(self, message):
            self.to_Notify = True
            self.message = message
        
        def apply_friction(self, rect:Rectangle):
            if self.on_surface(rect) and rect in self.for_rects:
                Fmax = rect.mass*self.g*self.coeff_of_friction
            else:
                return
            Fsum = np.zeros(2)
            for key in rect.forces:
                if key != 'Friction':
                    Fsum += rect.forces[key][0]
            if np.all(rect.vel==np.zeros(2)):
                if Fmax>= np.linalg.norm(Fsum):
                    Fmax = -Fsum
                    d = 1
                else:
                    d = -Fsum/np.linalg.norm(Fsum) if np.any(Fsum != np.zeros(2)) else np.zeros(2)
            else:
                d = -rect.vel/np.linalg.norm(rect.vel) if np.any(rect.vel != np.zeros(2)) else np.zeros(2)

            rect.forces['Friction'] = [Fmax*d, 'inf' ,np.zeros(2)]

        def apply_air_resistance(self, rect:Rectangle):
            if self.air and self.on_surface(rect) and np.any(rect.vel != np.zeros(2)) and rect in self.for_rects:
                normal_to_v = np.array([rect.vel[1], -rect.vel[0]])
                A = np.abs(np.dot(normal_to_v/np.linalg.norm(normal_to_v), rect.corners[0]-rect.corners[2]))
                rho = 1.225
                v2 = np.dot(rect.vel, rect.vel)
                Cd = 0.8
                d = -rect.vel/np.linalg.norm(rect.vel)
                F = d/2*A*rho*v2*Cd
                rect.forces['Air-resistance'] = [F, 'inf' ,np.zeros(2)]
        
        def notify(self, rect):
            if self.to_Notify and self.on_surface(rect):
                return self.message

    def __get_rect_name(self, rect):
        for key in self.__rects:
            if self.__rects[key] == rect:
                return key
    
    def __point_on_line(self, p1, p2, p3): # closest point on line p1-p2 to p3
        x1, y1 = p1[0], p1[1]
        x2, y2 = p2[0], p2[1]
        x3, y3 = p3[0], p3[1]
        dx, dy = x2-x1, y2-y1
        det = dx**2 + dy**2
        a = (dy*(y3-y1)+dx*(x3-x1))/det #solving the equations system for the two lines' intersection, 2nd line being p3 and along the normal to p1-p2
        return np.array([x1+a*dx, y1+a*dy])

    def __force_a_cal(self, rects, old_vs, dt):
        dp1 = -2*rects[1].mass/(rects[0].mass + rects[1].mass)*np.dot(old_vs[0]-old_vs[1], rects[0].pos-rects[1].pos)/(np.linalg.norm(rects[0].pos-rects[1].pos)**2)*(rects[0].pos-rects[1].pos)*rects[0].mass
        dp2 = -2*rects[0].mass/(rects[1].mass + rects[0].mass)*np.dot(old_vs[1]-old_vs[0], rects[1].pos-rects[0].pos)/(np.linalg.norm(rects[1].pos-rects[0].pos)**2)*(rects[1].pos-rects[0].pos)*rects[1].mass
        F1 = dp1/dt
        F2 = dp2/dt
        point_of_force = rects[0].pos-(rects[0].pos-rects[1].pos)/2
        point_on_rect = [None, None]
        for n, rect in enumerate(rects):
            point_on_rect[n] = self.__point_on_line(rect.corners[0], rect.corners[1], point_of_force)
            for i in range(1, 4):
                x = self.__point_on_line(rect.corners[i], rect.corners[(i+1)%4], point_of_force)
                if np.linalg.norm(x-point_of_force)<np.linalg.norm(point_on_rect[n]-point_of_force):
                    point_on_rect[n] = x
        a1 = point_on_rect[0]-rects[0].pos
        a2 = point_on_rect[1]-rects[1].pos
        return [F1, F2], [a1, a2]

    def __collision_check(self, rects):
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

    def __remove_rect_internal(self, rect:Rectangle):
        name = self.__get_rect_name(rect)
        del rect
        del self.__rects[name]

    def __blow_up(self, rect):
        self.__notification[self.__get_rect_name(rect)].append('Blown_up')
        self.__remove_rect_internal(rect)

    def __collision_detector(self, rects):
        rect_pairs = [[self.__rects[key1], self.__rects[key2]] for key1 in rects for key2 in rects if np.linalg.norm(self.__rects[key1].pos) < np.linalg.norm(self.__rects[key2].pos)]
        colliding = []
        with future.ThreadPoolExecutor() as ex:
            results = ex.map(self.__collision_check, rect_pairs)
            for r in results:
                if not r is None:
                    colliding.append(r)
        return colliding
        
    def __collision_handler(self, rects, vs, dt):
        e1 = -vs[0]/np.linalg.norm(vs[0]) if np.any(vs[0]!= np.zeros(2)) else np.zeros(2)
        e2 = -vs[1]/np.linalg.norm(vs[1]) if np.any(vs[1]!= np.zeros(2)) else np.zeros(2)
        if np.all(e1 == np.zeros(2)) and np.all(e2 == np.zeros(2)):
            raise Exception('Two rectangles without prior velocity are colliding')
        coll = self.__collision_check(rects)
        while not coll == None:
            rects[0].creep(e1, 1/self.__res)
            rects[1].creep(e2, 1/self.__res)
            coll = self.__collision_check(rects)
        
        Fs, As = self.__force_a_cal(rects, vs, dt)
        for i, rect in enumerate(rects):
            if not rect.destructable:
                rect.forces['Coll_F'] = [Fs[i], dt, As[i]]
            else:
                self.__blow_up(rect)
        
    def __collisions(self, old_vs, dt):
        collisions = self.__collision_detector(self.__rects)
        if not collisions is []:
            for pair in collisions:
                self.__collision_handler(pair, [old_vs[pair[0]], old_vs[pair[1]]], dt)

    def __update_rect(self, dt, old_v, rect):
        a = np.zeros(2)
        alpha = 0
        Dt = dt
        keys_to_delete = []
        for _, surface in self.__surfaces.items():
            surface.apply_friction(rect)
            surface.apply_air_resistance(rect)
        for name, force in rect.forces.items():
            if force[1] == 'inf':
                a += force[0]/rect.mass
                alpha += np.linalg.norm(np.cross(force[2], force[0]))/rect.momI
            elif force[1]<= dt:
                a += force[0]/rect.mass
                alpha += np.linalg.norm(np.cross(force[2], force[0]))/rect.momI
                Dt = force[1]
                if Dt < 0:
                    raise Exception('Negative time differance')
                keys_to_delete.append(name)
            else:
                a += force[0]/rect.mass
                alpha += np.linalg.norm(np.cross(force[2], force[0]))/rect.momI
                force[1] += -dt
        for key in keys_to_delete:
            rect.forces.pop(key)
        

        s = a/2*Dt**2
        theta = alpha/2*Dt**2
        mes = rect.move(dt, s, self.__res)
        if not mes is None:
            self.__notification[self.__get_rect_name(rect)].append(mes)
        mes = rect.rotate(dt, theta, self.__res)
        if not mes is None:
            self.__notification[self.__get_rect_name(rect)].append(mes)
        old_v[rect] = np.copy(rect.vel)
        rect.vel += a*Dt
        if np.linalg.norm(rect.vel) < 1/self.__res/10:
            rect.vel = np.zeros(2)
        rect.angle_vel += alpha*Dt
        if np.linalg.norm(rect.angle_vel) < np.pi/self.__res/10:
            rect.angle_vel = 0

        for _, surface in self.__surfaces.items():
            mes = surface.notify(rect)
            if not mes is None:
                self.__notification[self.__get_rect_name(rect)].append(mes)

    def update(self, dt):

        old_v = {}
        ovs = []
        dts = []
        rects = []
        for key in self.__rects:
            rects.append(self.__rects[key])
            ovs.append(old_v)
            dts.append(dt)
        with future.ThreadPoolExecutor() as ex:
            results = ex.map(self.__update_rect, dts, ovs, rects)
            for _ in results:
                pass
        
            

        self.__collisions(old_v, dt)
        notifications = self.__notification.copy()
        for key in self.__notification:
            self.__notification[key]=[]
        return notifications
        
    def gen_rect(self, name, w, h, m):
        if w==0 or h==0 or m==0:
            raise Exception("Width, height, or mass can't be zero")
        if name in self.__rects:
            raise Exception(f'Rectangle with the name {name} already exist')
        self.__rects[name] = self.Rectangle(w, h, m)
        self.__notification[name] = []

    def add_force(self, F, t, a, Fname, *names):
        for name in names:
            try:
                self.__rects[name].forces[Fname] = [F, t, a]
            except KeyError:
                raise Exception(f'There is no rectangle by the name {name}')

    def make_surface(self, S_name, coeff_fric, xrange, yrange, g, air, *names):
        rects = []
        if names == ():
            for _, val in self.__rects.items():
                rects.append(val)
        else:
            for name in names:
                try:
                    rects.append(self.__rects[name])
                except KeyError:
                    raise Exception(f'There is no rectangle by the name {name}')
        self.__surfaces[S_name] = self.Surface(coeff_fric, xrange, yrange, g, air, rects)

    def place_rect(self, name, pos):
        try:
            self.__rects[name].move_to(pos)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')

    def rotate_rect(self, name, theta):
        try:
            self.__rects[name].rotate_to(theta)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')
    
    def get_vel(self, name):
        try:
            return np.copy(self.__rects[name].vel)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')
    
    def get_pos(self, name):
        try:
            return np.copy(self.__rects[name].pos)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')
    
    def get_angle(self, name):
        try:
            return np.copy(self.__rects[name].angle)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')

    def get_angle_vel(self, name):
        try:
            return np.copy(self.__rects[name].angle_vel)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')

    def make_immoveable(self, name):
        try:
            self.__rects[name].moveability(False)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')
    
    def make_moveable(self, name):
        try:
            self.__rects[name].moveability(True)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')
    
    def make_destructable(self, name):
        try:
            self.__rects[name].destructability(True)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')
    
    def make_indestructable(self, name):
        try:
            self.__rects[name].destructability(False)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')
    
    def set_vel(self, name, v):
        try:
            self.__rects[name].set_vel(v)
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')

    def remove_rect(self, name):
        try:
            self.__remove_rect_internal(self.__rects[name])
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')

    def blowup_rect(self, name):
        try:
            self.__blow_up(self.__rects[name])
        except KeyError:
            raise Exception(f'There is no rectangle by the name {name}')
    
    def add_notification(self, S_name, message):
        try:
            self.__surfaces[S_name].add_notify(message)
        except KeyError:
            raise Exception(f'There is no surface by the name {S_name}')
