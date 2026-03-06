import os
import tkinter as tk
from ui.main_window import MainWindow

BASE_DIR = os.path.dirname(__file__)
BULLETIN_DIR = os.path.join(BASE_DIR, "bulletins")

root = tk.Tk()
app = MainWindow(root, BULLETIN_DIR)
root.mainloop()