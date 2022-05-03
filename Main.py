import tkinter as tk

window = tk.Tk()
window.geometry('1000x700')
window.resizable(width=False, height=False)
controls = tk.Frame(window, width=250, height=700)
box = tk.Canvas(window, width=750, height=700, bg='white')
button_start = tk.Button(controls, text='Start!')
button_stop = tk.Button(controls, text='Abort!')
button_start.grid(row=0, column=0, sticky='ew')
button_stop.grid(row=0, column=1, sticky='ew')
controls.grid(row=0, column=1)
box.grid(row=0, column=0)

window.mainloop()