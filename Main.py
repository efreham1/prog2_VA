import tkinter as tk
from pysiks import Physics_Canvas as PC
from PIL import Image, ImageTk
import numpy as np
import random
from time import perf_counter as pc

class Car:

    def __init__(self, canvas:tk.Canvas, physics_canvas:PC, filepath, ppm, name) -> None:
        self.__tk_canvas = canvas
        self.__phy_can = physics_canvas
        self.__ppm = ppm
        self.__image = Image.open(filepath).resize((2*self.__ppm, 4*self.__ppm))
        self.__image_angle = 0
        self.__name = name
        self.__mass = 1000
        self.__phy_can.gen_rect(self.__name, 2, 4, self.__mass)
        self.__phy_can.make_destructable(self.__name)
        self.__base_power = 400000. #W
        self.__base_launch_force = 10000.
        self.__power_mod = 1
        self.__launch_mod = 1
        self.__power = self.__base_power*self.__power_mod
        self.__launch_force = self.__base_launch_force*self.__launch_mod
        self.__running = False
        self.__tkimage = ImageTk.PhotoImage(self.__image)
        self.object = self.__tk_canvas.create_image(0, 0, image=self.__tkimage)

    def __coordinate_to_pixel(self, pos):
        return round(pos[0]*self.__ppm)+950, round(-pos[1]*self.__ppm)+175

    def __get_F(self):
        v = np.linalg.norm(self.__phy_can.get_vel(self.__name))
        fmax = self.__power/v if v!= 0 else 1
        v_fmax = 40
        if v > v_fmax:
            v_fmax = v
        f = ((v_fmax-v)*self.__launch_force+v*fmax)/v_fmax
        F = f*np.array([-np.sin(self.__phy_can.get_angle(self.__name)), np.cos(self.__phy_can.get_angle(self.__name))])
        return F
    

    def __get_random(self, mod):
        x = np.random.exponential()
        limit = 3.8*(5-mod*2)
        if x > limit:
            return True
        else:
            return False
    def __check_accident(self):
        if self.__get_random(self.__power_mod):
            self.__phy_can.blowup_rect(self.__name)
        if self.__get_random(self.__launch_mod):
            byte = random.randbytes(1)
            a = 3*np.array([-np.sin(self.__phy_can.get_angle(self.__name)), np.cos(self.__phy_can.get_angle(self.__name))])
            f = 1000
            if byte:
                self.__phy_can.add_force(f*np.array([np.cos(self.__phy_can.get_angle(self.__name)), np.sin(self.__phy_can.get_angle(self.__name))]), 0.5, a, 'oof', self.__name)
            else:
                self.__phy_can.add_force(np.array([-np.cos(self.__phy_can.get_angle(self.__name)), np.sin(self.__phy_can.get_angle(self.__name))]), 0.5, a, 'oof', self.__name)
    
    def update_car(self, dt):
        if self.__running:
            self.__phy_can.add_force(self.__get_F(), 'inf', np.zeros(2), 'Engine', self.__name)
            self.__check_accident()
    
    def update_graphics(self):
        angle = self.__phy_can.get_angle(self.__name)
        self.__image = self.__image.rotate((angle-self.__image_angle)/np.pi*180, expand=1)
        self.__image_angle = angle
        self.__tk_canvas.delete(self.object)
        self.__tkimage = ImageTk.PhotoImage(self.__image)
        x,y = self.__coordinate_to_pixel(self.__phy_can.get_pos(self.__name))
        self.object = self.__tk_canvas.create_image(x, y, image=self.__tkimage)
    
    def place(self, pos, angle):
        self.__phy_can.place_rect(self.__name, pos)
        self.__phy_can.rotate_rect(self.__name, angle)
        self.__image_angle = self.__phy_can.get_angle(self.__name)
        self.__image = self.__image.rotate(self.__image_angle/np.pi*180, expand=1)
        self.__tk_canvas.delete(self.object)
        self.__tkimage = ImageTk.PhotoImage(self.__image)
        x,y = self.__coordinate_to_pixel(self.__phy_can.get_pos(self.__name))
        self.object = self.__tk_canvas.create_image(x, y, image=self.__tkimage)

    def start_engine(self):
        self.__running = True

        
class Wall:

    def __init__(self, canvas:tk.Canvas, physics_canvas:PC, filepath, ppm, name, xrange, yrange) -> None:
        self.__tk_canvas = canvas
        self.__phy_can = physics_canvas
        self.__ppm = ppm
        self.__image = ImageTk.PhotoImage(Image.open(filepath).resize((abs(xrange[1]-xrange[0]), abs(yrange[1]-yrange[0]))))
        self.__name = name
        self.__mass = 1000*abs(xrange[1]-xrange[0])/self.__ppm*abs(yrange[1]-yrange[0])/self.__ppm
        self.__phy_can.gen_rect(self.__name, abs(xrange[1]-xrange[0])/self.__ppm, abs(yrange[1]-yrange[0])/self.__ppm, self.__mass)
        self.__phy_can.make_indestructable(self.__name)
        self.__phy_can.make_immoveable(self.__name)
        self.__phy_can.place_rect(self.__name, self.__pixelrange_to_coordinate(xrange, yrange))

        x, y = xrange[0]+(xrange[1]-xrange[0])/2, yrange[0]+(yrange[1]-yrange[0])/2
        self.object = self.__tk_canvas.create_image(x, y, image=self.__image)

    def __pixelrange_to_coordinate(self, xrange, yrange):
        return np.array([(xrange[0]-950+(xrange[1]-xrange[0])/2)/self.__ppm, (-yrange[0]+175-(yrange[1]-yrange[0])/2)/self.__ppm])



class Background:

    def __init__(self, canvas:tk.Canvas, physics_canvas:PC, filepath, xrange, yrange, fric_coeff, name, ppm, air) -> None:
        self.__tk_canvas = canvas
        self.__phy_can = physics_canvas
        self.__ppm = ppm
        self.__image = ImageTk.PhotoImage(Image.open(filepath).resize((abs(xrange[1]-xrange[0]), abs(yrange[1]-yrange[0]))))
        self.__name = name
        new_xrange, new_yrange = self.__pixelrange_to_cooridanterange(xrange, yrange)
        self.__phy_can.make_surface(self.__name, fric_coeff, new_xrange, new_yrange, 9.82, air)

        x, y = xrange[0]+(xrange[1]-xrange[0])/2, yrange[0]+(yrange[1]-yrange[0])/2
        self.object = self.__tk_canvas.create_image(x, y, image=self.__image)

    def __pixelrange_to_cooridanterange(self, xrange, yrange):
        return [(xrange[0]-950)/self.__ppm, (xrange[1]-950)/self.__ppm], [(-yrange[1]+175)/self.__ppm, (-yrange[0]+175)/self.__ppm]

    def add_notification(self, message):
        self.__phy_can.add_notification(self.__name, message)

def start_race(dt, cars, physics, canvas):
    canvas.after(int(dt*1000), update_everything, dt, cars, physics, canvas)

def update_everything(dt, cars, physics, canvas):
    start = pc()
    for car in cars:
        car.update_car(dt)
    physics.update(dt)
    for car in cars:
        car.update_graphics()
    end = pc()
    time_diff = end-start
    if time_diff > dt:
        time_diff = dt-0.001
    canvas.after(int(dt*1000-time_diff*1000), update_everything, dt, cars, physics, canvas)
    
window = tk.Tk()
window.geometry('1900x700')
window.resizable(width=False, height=False)
controls = tk.Frame(window, width=1900, height=350)
box = tk.Canvas(window, width=1900, height=350, bg='white')

button_start = tk.Button(controls, text='Start!')
button_stop = tk.Button(controls, text='Abort!')
button_start.grid(row=0, column=0)
button_stop.grid(row=0, column=1)

controls.grid(row=1, column=0)
box.grid(row=0, column=0)


physics = PC(100)
car1 = Car(box, physics, 'GitHub local repositories\prog2_VA\Elements\Blue car.png', 4, 'Blue car')
car2 = Car(box, physics, 'GitHub local repositories\prog2_VA\Elements\Red car.png', 4, 'Red car')
track = Background(box, physics, 'GitHub local repositories\prog2_VA\Elements\Track.png', [0, 1900], [150, 200], 0.02, 'Track', 4, True)
gravel_below = Background(box, physics, 'GitHub local repositories\prog2_VA\Elements\Dirt.png', [0, 1900], [200, 240], 0.2, 'Gravel1', 4, True)
gravel_above = Background(box, physics, 'GitHub local repositories\prog2_VA\Elements\Dirt.png', [0, 1900], [110, 150], 0.2, 'Gravel2', 4, True)
grass_below = Background(box, physics, 'GitHub local repositories\prog2_VA\Elements\Grass.png', [0, 1900], [240, 350], 0.1, 'Grass1', 4, True)
grass_above = Background(box, physics, 'GitHub local repositories\prog2_VA\Elements\Grass.png', [0, 1900], [0, 110], 0.1, 'Grass2', 4, True)
finnish_line = Background(box, physics, 'GitHub local repositories\prog2_VA\Elements\line.png', [1820, 2200], [145, 205], 0, 'Finnishline', 4, False)
finnish_line.add_notification('Finnished')
wall_above = Wall(box, physics, 'GitHub local repositories\prog2_VA\Elements\Wall.png', 4, 'wall1', [0, 1900], [0, 70])
wall_below = Wall(box, physics, 'GitHub local repositories\prog2_VA\Elements\Wall.png', 4, 'wall2', [0, 1900], [280, 350])
car1.place(np.array([-237, 3]), -np.pi/2)
car2.place(np.array([-237, -3]), -np.pi/2)



car1.start_engine()
car2.start_engine()
start_race(0.1, [car1, car2], physics, box)

window.mainloop()