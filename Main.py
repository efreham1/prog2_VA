import tkinter as tk

window = tk.Tk()
window.geometry('1100x800')
window.resizable(width=False, height=False)
controls = tk.Frame(window, width=300, height=800)
box = tk.Canvas(window, width=800, height=800, bg='white')
button_start = tk.Button(controls, text='Start!')
button_stop = tk.Button(controls, text='Abort!')
button_start.grid(row=0, column=0, sticky='ew')
button_stop.grid(row=0, column=1, sticky='ew')
controls.grid(row=0, column=1)
box.grid(row=0, column=0)

window.mainloop()