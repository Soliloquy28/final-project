from __future__ import print_function
import tkinter as tk
from tkinter import messagebox
import Global


# Login Page frame class
class LoginPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master, width=700, height=500)
        photo_ucl = Global.photo_place("ucl_logo.png", 150, 60)
        self.image_label_ucl = tk.Label(self, image=photo_ucl)
        self.image_label_ucl.image = photo_ucl
        self.image_label_ucl.place(relx=0.5, rely=0.1, anchor="n")
        self.username_label = tk.Label(self, text="Username:")
        self.username_label.place(relx=0.5, rely=0.35, anchor='center')
        self.username_entry = tk.Entry(self, textvariable=self.master.username)
        self.username_entry.place(relx=0.5, rely=0.5, anchor='center')
        self.enter_button = tk.Button(self, text="Enter", command=self.check_username, cursor="hand2")
        self.enter_button.place(relx=0.5, rely=0.7, anchor='center')
        # When closing the main window, the program quits automatically
        self.master.protocol("WM_DELETE_WINDOW", self.quit)
        self.pack()


    # Check for valid entered username
    def check_username(self):
        from ModePage import ModePage
        username = self.master.username.get().strip()
        if not username:
            messagebox.showwarning("Warning", "Please enter valid username")
        else:
            self.master.show_frame(ModePage)