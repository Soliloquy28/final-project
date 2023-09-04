from __future__ import print_function
import tkinter as tk
from tkinter import messagebox
import os


# Mode Page frame class
class ModePage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.welcome_label = tk.Label(self, text="")
        self.welcome_label.place(relx=0.5, rely=0.2, anchor='center')

        self.new_button = tk.Button(self, text="Start A New Project", command=self.go_to_upload_page, cursor="hand2")
        self.new_button.place(relx=0.5, rely=0.4, anchor='center')

        self.continue_button = tk.Button(self, text="Continue A Project", command=self.go_to_continue_page, cursor="hand2")
        self.continue_button.place(relx=0.5, rely=0.6, anchor='center')

        self.back_button = tk.Button(self, text="Back", command=self.back_to_login_page, cursor="hand2")
        self.back_button.place(relx=0.05, rely=0.05, anchor='nw')

        self.master.protocol("WM_DELETE_WINDOW", self.quit)

        print(type(self.welcome_label))
        print(type(self.new_button))

    def go_to_upload_page(self):
        from UploadPage import UploadPage
        # self.master.repository_path_dynamic = ""
        self.master.selected_new == ""
        self.master.experiment_path_dynamic = ""
        self.master.source_video_path_dynamic = ""
        self.master.processed_video_path_dynamic = ""
        self.master.basement_name_dynamic = ""
        self.master.selected_exp == ""
        self.master.show_frame(UploadPage)


    def go_to_continue_page(self):
        from ContinuePage import ContinuePage
        directory_path = os.path.abspath(os.getcwd())
        if "Repository" not in os.listdir(directory_path):
            messagebox.showwarning("Warning", "Sorry there is no project to continue.")
        else:
            repository_path = f'{directory_path}/Repository'
            for item in os.listdir(repository_path):
                if len(os.listdir(repository_path)) == 1 and item == ".DS_Store":
                    messagebox.showwarning("Warning", "Sorry there is no project to continue.")
                else:
                    self.master.show_frame(ContinuePage)


    def back_to_login_page(self):
        from LoginPage import LoginPage
        self.master.show_frame(LoginPage)


    def update_username(self):
        self.welcome_label.config(text=f"Welcome, {self.master.username.get().strip()}")