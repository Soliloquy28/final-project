from __future__ import print_function
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import json


# Continue Page frame class
class ContinuePage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        self.continue_label = tk.Label(self, text="Please select the username of the project: ")
        self.continue_label.place(relx=0.5, rely=0.25, anchor='center')
        self.continue_dropdown = ttk.Combobox(self, values=self.master.continue_author_list)
        self.continue_dropdown.bind("<<ComboboxSelected>>", self.on_select)
        self.continue_dropdown.place(relx=0.5, rely=0.4, anchor='center')
        self.enter_button = tk.Button(self, text="Enter", command=self.go_to_experiment_page, cursor="hand2")
        self.enter_button.place(relx=0.5, rely=0.75, anchor='center')
        self.back_button = tk.Button(self, text="Back", command=self.back_to_mode_page, cursor="hand2")
        self.back_button.place(relx=0.05, rely=0.05, anchor='nw')

        self.master.protocol("WM_DELETE_WINDOW", self.quit)


    # Bind on_select to ComboboxSelected event
    def on_select(self, event):
        self.master.continue_username = self.continue_dropdown.get()


    def go_to_experiment_page(self):
        from ExperimentPage import ExperimentPage
        selected_username = self.continue_dropdown.get()
        if not selected_username:
            messagebox.showwarning("Warning", "Please select a valid username.")
        else:
            self.master.continue_username = selected_username
            self.master.show_frame(ExperimentPage)


    def back_to_mode_page(self):
        from ModePage import ModePage
        self.master.show_frame(ModePage)


    def update_available(self):
        if self.master.continue_username not in self.master.continue_author_list:
            self.continue_dropdown.set('')
        directory_path = os.path.abspath(os.getcwd())
        if "Repository" not in os.listdir(directory_path):
            os.makedirs(f'{directory_path}/Repository')
        repository_path = f'{directory_path}/Repository'
        self.master.repository_path_dynamic = repository_path
        for dir in os.listdir(repository_path):
            if dir.startswith("Experiment"):
                exp_path = f"{repository_path}/{dir}"
                for root, dirs, files in os.walk(exp_path):
                    for file in files:
                        if file.endswith(".json") and file.startswith("metadata"):
                            with open(f"{exp_path}/{file}", "r") as f:
                                data = json.load(f)
                            continue_author = data['author']
                            if continue_author not in self.master.continue_author_list:
                                self.master.continue_author_list.append(continue_author)
        self.continue_dropdown['values'] = self.master.continue_author_list