import tkinter as tk
from pysiks import Physics_Canvas as PC
from PIL import Image, ImageTk

class Car:

    def __init__(self, canvas:tk.Canvas, physics_canvas:PC, filepath, scale, name) -> None:
        self.tk_canvas = canvas
        self.phy_can = physics_canvas
        self.image = Image.open(filepath).resize((round(1.5*self.ppm), 3*self.ppm))
        self.ppm = scale
        self.name = name
        self.mass = 1000
        self.phy_can.gen_rect(self.name, round(1.5*self.ppm), 3*self.ppm, self.mass)
        self.power = 50000 #W
        self.front_wheel_size = 1
        self.torque = 

    def get_F(self):
        v = self.phy_can.get_vel(self.name)
        if v < 10:
            v = 0.1
        else:
            return self.power/v

class Background:

    def __init__(self, canvas:tk.Canvas, physics_canvas:PC, filepath) -> None:
        self.tk_canvas = canvas
        self.phy_can = physics_canvas
        self.image = Image.open(filepath)

window = tk.Tk()
window.geometry('1000x700')
window.resizable(width=False, height=False)
controls = tk.Frame(window, width=250, height=700)
box = tk.Canvas(window, width=750, height=700, bg='white')

button_start = tk.Button(controls, text='Start!')
button_stop = tk.Button(controls, text='Abort!')
button_start.grid(row=0, column=0)
button_stop.grid(row=0, column=1)

controls.grid(row=0, column=1)
box.grid(row=0, column=0)

image = Image.open('GitHub local repositories\prog2_VA\Elements\Blue car.png')
image = image.resize((100, 100))
tk_image = ImageTk.PhotoImage(image)
img = box.create_image(250, 120, anchor='nw', image=tk_image)

window.mainloop()