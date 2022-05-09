"""
Date: 22-09-05
Name: Fredrik Hammarberg
Mail: Hammarberg83@gmail.com
Presented to: Julia Sulyaeva
"""
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
        self.name = name
        self.__mass = 1000
        self.__phy_can.gen_rect(self.name, 2, 4, self.__mass)
        self.__phy_can.make_destructable(self.name)
        self.__base_power = 400000. #W
        self.__base_launch_force = 10000.
        self.__power_mod = 1.25
        self.__launch_mod = 0.8
        self.__power = self.__base_power*self.__power_mod
        self.__launch_force = self.__base_launch_force*self.__launch_mod
        self.__running = False
        self.__tkimage = ImageTk.PhotoImage(self.__image)
        self.object = self.__tk_canvas.create_image(0, 0, image=self.__tkimage)
        self.__is_player_car = False

    def __coordinate_to_pixel(self, pos):
        return round(pos[0]*self.__ppm)+950, round(-pos[1]*self.__ppm)+175

    def __get_F(self):
        v = np.linalg.norm(self.__phy_can.get_vel(self.name))
        fmax = self.__power/v if v!= 0 else 1
        v_fmax = 40
        if v > v_fmax:
            v_fmax = v
        f = ((v_fmax-v)*self.__launch_force+v*fmax)/v_fmax
        F = f*np.array([-np.sin(self.__phy_can.get_angle(self.name)), np.cos(self.__phy_can.get_angle(self.name))])
        return F
    

    def __get_random(self, mod):
        x = random.uniform(0, 100*10000**2/10000**mod)
        limit = 20
        if x < limit:
            return True
        else:
            return False
    def __check_accident(self):
        if self.__get_random(self.__power_mod):
            self.__phy_can.blowup_rect(self.name)
        if self.__get_random(self.__launch_mod):
            left_right = random.randint(0, 1)
            a = 50*np.array([-np.sin(self.__phy_can.get_angle(self.name)), np.cos(self.__phy_can.get_angle(self.name))])
            f = 100
            if left_right == 1:
                F = f*np.array([np.cos(self.__phy_can.get_angle(self.name)), np.sin(self.__phy_can.get_angle(self.name))])
                self.__phy_can.add_force(F, 1, a, 'oof', self.name)
            elif left_right == 0:
                F = f*np.array([-np.cos(self.__phy_can.get_angle(self.name)), -np.sin(self.__phy_can.get_angle(self.name))])
                self.__phy_can.add_force(F, 1, a, 'oof', self.name)

    
    def update_car(self, info):
        if self.__is_player_car:
            self.change_modifiers(info['power'].get()/100, info['launch'].get()/100)
        if self.__running:
            self.__phy_can.add_force(self.__get_F(), 'inf', np.zeros(2), 'Engine', self.name)
            self.__check_accident()
    
    def update_graphics(self):
        angle = self.__phy_can.get_angle(self.name)
        self.__image = self.__image.rotate((angle-self.__image_angle)/np.pi*180, expand=1)
        self.__image_angle = angle
        self.__tk_canvas.delete(self.object)
        self.__tkimage = ImageTk.PhotoImage(self.__image)
        x,y = self.__coordinate_to_pixel(self.__phy_can.get_pos(self.name))
        self.object = self.__tk_canvas.create_image(x, y, image=self.__tkimage)
    
    def place(self, pos, angle):
        self.__phy_can.place_rect(self.name, pos)
        self.__phy_can.rotate_rect(self.name, angle)
        self.__image_angle = self.__phy_can.get_angle(self.name)
        self.__image = self.__image.rotate(self.__image_angle/np.pi*180, expand=1)
        self.__tk_canvas.delete(self.object)
        self.__tkimage = ImageTk.PhotoImage(self.__image)
        x,y = self.__coordinate_to_pixel(self.__phy_can.get_pos(self.name))
        self.object = self.__tk_canvas.create_image(x, y, image=self.__tkimage)

    def start_engine(self):
        self.__running = True

    def change_modifiers(self, pow_mod, launch_mod):
        self.__launch_mod = launch_mod
        self.__power_mod = pow_mod
        self.__power = self.__base_power*self.__power_mod
        self.__launch_force = self.__base_launch_force*self.__launch_mod
    
    def delete_it(self):
        self.__phy_can.remove_rect(self.name)
        self.__tk_canvas.delete(self.object)
        del self
    
    def make_player_car(self):
        self.__is_player_car = True

    def who_won(self):
        return self.__phy_can.get_pos(self.name)[0]+237

        
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

def start_race(info):
    info['race_running'] = True
    info['canvas'].after(int(info['dt']*1000), update_everything, info)
    button_start['state'] = "disabled"
    change_launch['state'] = "disabled"
    change_power['state'] = "disabled"

def update_everything(info):
    if info['race_running']:
        start = pc()
        for car in info['cars']:
            car.update_car(info)
        notifications = physics.update(info['dt'])       
        for rect_name, messages in notifications.items():
            for message in messages:
                if message == 'Blown_up':
                    for car in info['cars']:
                        if car.name == rect_name:
                            correct_car = car
                    pos = info['canvas'].coords(correct_car.object)
                    info['cars'].pop(info['cars'].index(correct_car))
                    info['explosions'].append(info['canvas'].create_image(pos[0], pos[1], image=explosion))
                    del correct_car
                elif message == 'Finnished':
                    info['race_running'] = False
                    info['victory'] = True
        for car in info['cars']:
            car.update_graphics()
        if info['victory']:
            victory(info)
        end = pc()
        time_diff = end-start
        if time_diff > info['dt']:
            time_diff = info['dt']-0.001
        info['canvas'].after(int(info['dt']*1000), update_everything, info)


def victory(info):
    car1 = info['cars'][0].who_won()
    if len(info['cars']) == 2:
        car2 = info['cars'][1].who_won()
    else:
        car2 = -237
    if car1 > car2:
        text = f"The {info['cars'][0].name} has won!"
    elif car1 < car2:
        text = f"The {info['cars'][1].name} has won!"
    else:
        text = 'The race was a tie!'
    popup = tk.Toplevel(info['window'])
    popup.geometry('250x150')
    tk.Label(popup, text= f'{text}\n Do you wish to reset or quit?').place(x=30, y=10)
    tk.Button(popup, text= 'Reset', command=lambda:reset(info, popup)).place(x=30, y=70)
    tk.Button(popup, text= 'Quit', command=info['window'].destroy).place(x=180, y=70)


def setup(canvas, physics_can, dt, window, power, launch):
    info = {}
    info['power'] = power
    info['launch'] = launch
    info['window'] = window
    info['canvas'] = canvas
    info['physics'] = physics_can
    info['dt'] = dt
    info['cars'] = [Car(canvas, physics_can, 'prog2_VA\Elements\Blue car.png', 4, 'Blue car'), Car(canvas, physics_can, 'prog2_VA\Elements\Red car.png', 4, 'Red car')]
    info['track'] = Background(canvas, physics_can, 'prog2_VA\Elements\Track.png', [0, 1900], [150, 200], 0.02, 'Track', 4, True)
    info['gravel_below'] = Background(canvas, physics_can, 'prog2_VA\Elements\Dirt.png', [0, 1900], [200, 240], 0.2, 'Gravel1', 4, True)
    info['gravel_above'] = Background(canvas, physics_can, 'prog2_VA\Elements\Dirt.png', [0, 1900], [110, 150], 0.2, 'Gravel2', 4, True)
    info['grass_below'] = Background(canvas, physics_can, 'prog2_VA\Elements\Grass.png', [0, 1900], [240, 350], 0.1, 'Grass1', 4, True)
    info['grass_above'] = Background(canvas, physics_can, 'prog2_VA\Elements\Grass.png', [0, 1900], [0, 110], 0.1, 'Grass2', 4, True)
    info['finnish_line'] = Background(canvas, physics_can, 'prog2_VA\Elements\line.png', [1820, 2200], [145, 205], 0, 'Finnishline', 4, False)
    info['finnish_line'].add_notification('Finnished')
    info['wall_above'] = Wall(canvas, physics_can, 'prog2_VA\Elements\Wall.png', 4, 'wall1', [0, 1900], [0, 70])
    info['wall_below'] = Wall(canvas, physics_can, 'prog2_VA\Elements\Wall.png', 4, 'wall2', [0, 1900], [280, 350])
    info['cars'][0].place(np.array([-237, 3]), -np.pi/2)
    info['cars'][1].place(np.array([-237, -3]), -np.pi/2)
    info['race_running'] = False
    info['explosions'] = []
    info['victory'] = False
    return info

def reset(info:dict, *popup):
    info['race_running'] = False
    info['victory'] = False
    for expl in info['explosions']:
        info['canvas'].delete(expl)
    for car in info['cars']:
        car.delete_it()
    info['cars'] = [Car(info['canvas'], info['physics'], 'prog2_VA\Elements\Blue car.png', 4, 'Blue car'), Car(info['canvas'], info['physics'], 'prog2_VA\Elements\Red car.png', 4, 'Red car')]
    info['cars'][0].place(np.array([-237, 3]), -np.pi/2)
    info['cars'][1].place(np.array([-237, -3]), -np.pi/2)
    info['cars'][0].start_engine()
    info['cars'][1].make_player_car()
    if popup != ():
        popup[0].destroy()
    button_start['state'] = "normal"
    change_launch['state'] = "normal"
    change_power['state'] = "normal"

def start_player_engine(info):
    info['cars'][1].start_engine()

def main():
    info['cars'][0].start_engine()
    info['cars'][1].make_player_car()
    window.mainloop()





if __name__ == '__main__':
    
    window = tk.Tk()
    physics = PC(10)
    window.geometry('1900x700')
    window.resizable(width=False, height=False)
    controls = tk.Frame(window, width=1900, height=350)
    box = tk.Canvas(window, width=1900, height=350, bg='white')
    explosion = ImageTk.PhotoImage(Image.open('prog2_VA\Elements\Explosion.png'))
    change_power = tk.Scale(controls, from_=0, to=200, orient='horizontal')
    change_launch = tk.Scale(controls, from_=0, to=200, orient='horizontal')
    info = setup(box, physics, 0.1, window, change_power, change_launch)

    button_start = tk.Button(controls, text='Start!', command=lambda: start_race(info))
    button_stop = tk.Button(controls, text='Abort!', command=lambda: reset(info))
    button_egnition = tk.Button(controls, text='Start engine', command=lambda: start_player_engine(info))
    power_label = tk.Label(controls, text='Engine power:')
    launch_label = tk.Label(controls, text='Engine torque:')
    button_start.grid(row=0, column=0)
    button_stop.grid(row=0, column=1)
    button_egnition.grid(row=0, column=2)
    change_power.grid(row=2, column=0)
    power_label.grid(row=1, column=0)
    change_launch.grid(row=2, column=1)
    launch_label.grid(row=1, column=1)

    controls.grid(row=1, column=0)
    box.grid(row=0, column=0)

    main()

