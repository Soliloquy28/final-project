from __future__ import print_function
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import os
import shutil
import json


# Experiment Page frame class
class ExperimentPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)

        # Initialize sorting column and direction
        self.sort_column = None
        self.sort_direction = False

        self.continue_project_label = tk.Label(self, text="")
        self.continue_project_label.place(relx=0.5, rely=0.15, anchor='center')

        # Create a frame for the Treeview and Scrollbar
        self.tree_frame = tk.Frame(self)
        self.tree_frame.place(relx=0.5, rely=0.5, anchor='center')
        self.tree = ttk.Treeview(self.tree_frame, columns=("c1", "c2", "c3", "c4"), show='headings', selectmode="extended", height=14)
        self.tree.column("c1", anchor=tk.CENTER, width=100)
        self.tree.heading("c1", text="Experiment", command=lambda _col="c1": self.sortby(_col, 0))
        self.tree.column("c2", anchor=tk.CENTER, width=200)
        self.tree.heading("c2", text="Video Name", command=lambda _col="c2": self.sortby(_col, 0))
        self.tree.column("c3", anchor=tk.CENTER, width=150)
        self.tree.heading("c3", text="Time Created", command=lambda _col="c3": self.sortby(_col, 0))
        self.tree.column("c4", anchor=tk.CENTER, width=100)
        self.tree.heading("c4", text="Status", command=lambda _col="c4": self.sortby(_col, 0))

        self.tree.pack(side=tk.LEFT)
        # Create a vertical scrollbar
        self.tree_vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        self.tree_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # Configure the treeview to use the scrollbar
        self.tree.configure(yscrollcommand=self.tree_vsb.set)

        self.delete_all_btn = tk.Button(self, text="Delete All", command=self.delete_all_own_experiment, cursor="hand2")
        self.delete_experiment_btn = tk.Button(self, text="Delete Selected Experiment(s)", command=self.delete_selected_experiment, cursor="hand2")
        self.continue_button = tk.Button(self, text="Go To Processing Page", command=self.go_to_processing_page, cursor="hand2")
        self.back_button = tk.Button(self, text="Back", command=self.back_to_continue_page, cursor="hand2")
        self.back_button.place(relx=0.05, rely=0.05, anchor='nw')

        self.master.protocol("WM_DELETE_WINDOW", self.quit)


    def delete_selected_experiment(self):
        selected_item = self.tree.selection()
        # If none is selected and directly clicked delete
        if len(selected_item) > 0:
            choice = messagebox.askyesno("Confirmation", "Are you sure you want to delete the selected experiment(s)?")
            if choice:
                directory_path = os.path.abspath(os.getcwd())
                repository_path = f'{directory_path}/Repository'
                for item_id in selected_item:
                    item_values = self.tree.item(item_id, "values")
                    experiment_selected = item_values[0]
                    # Delete the experiment folder
                    experiment_path = f'{repository_path}/{experiment_selected}'
                    if experiment_path and os.path.exists(experiment_path):
                        shutil.rmtree(experiment_path)
                    # Delete from treeview
                    self.tree.delete(item_id)
                    self.update_sort()
                if not self.tree.get_children():
                    self.master.continue_author_list.remove(self.master.continue_username)
        else:
            messagebox.showwarning("Warning", "Please select at least one experiment.")


    def delete_all_own_experiment(self):
        choice = messagebox.askyesno("Confirmation", "Are you sure you want to delete all your experiment(s)?")
        if choice:
            directory_path = os.path.abspath(os.getcwd())
            repository_path = f'{directory_path}/Repository'
            for item in self.tree.get_children():
                item_values = self.tree.item(item, "values")
                experiment_selected = item_values[0]
                # Delete the experiment folder
                experiment_path = f'{repository_path}/{experiment_selected}'
                if experiment_path and os.path.exists(experiment_path):
                    shutil.rmtree(experiment_path)
                # Clear the treeview
                self.tree.delete(item)
            if not self.tree.get_children():
                self.master.continue_author_list.remove(self.master.continue_username)
            self.update_sort()

    def sortby(self, col, descending):
        # Save the data of the clicked column
        data = []
        is_num = True
        for child in self.tree.get_children(''):
            data.append((self.tree.set(child, col), child))
            if is_num:
                if not self.is_num(data[-1][0]):
                    is_num = False

        def to_experiment(s):
            try:
                count = s[0].split('Experiment_')[1]
                count = float(count)
                return count
            except:
                return s

        if col == 'c1':
            # Special handling for Experiment
            data = sorted(data, key=to_experiment, reverse=descending)
        elif is_num:
            # Special handling if it's purely numeric
            data = sorted(data, key=lambda x: (float(x[0]), x[1]), reverse=descending)
        else:
            # Ignore alphabet case for sorting
            data = sorted(data, key=lambda x: (x[0].lower(), x[1]), reverse=descending)
        # Update the sorted data
        for indx, item in enumerate(data):
            self.tree.move(item[1], '', indx)
        self.tree.heading(col, command=lambda _col=col: self.sortby(col, int(not descending)))
        # Save sorting column and direction for future use,
        # allowing the original sorting to be displayed when inserting new data
        self.sort_column = col
        self.sort_direction = descending

    def update_sort(self):
        # If no sorting has been performed, default to sorting by time
        if not self.sort_column:
            self.sort_column = 'c3'
            self.sort_direction = True
        # If sorting is already set, reapply the current sorting
        self.sortby(self.sort_column, self.sort_direction)

    # Test if the string contains only digits
    def is_num(self, ss):
        try:
            float(ss)
            return True
        except:
            return False

    def update_username_and_list(self):
        # Remove all buttons first
        self.delete_all_btn.place_forget()
        self.delete_experiment_btn.place_forget()
        self.continue_button.place_forget()
        if self.master.continue_username == self.master.username.get().strip():
            self.delete_all_btn.place(relx=0.8, rely=0.05, anchor='nw')
            self.delete_experiment_btn.place(relx=0.25, rely=0.9, anchor='center')
            self.continue_button.place(relx=0.8, rely=0.9, anchor='center')
        else:
            self.continue_button.place(relx=0.5, rely=0.9, anchor='center')
        self.continue_project_label.config(text=f"Please choose one project from {self.master.continue_username}: ")
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
                            if data['author'] == self.master.continue_username:
                                experiment = data["experiment"]
                                if experiment not in self.master.exp_list:
                                    self.master.exp_list.append(experiment)
                                    video_name = data["videoname"]
                                    time_created = data["timecreate"]
                                    status = data["status"]
                                    metadata_list = [experiment, video_name, time_created, status]
                                    self.tree.insert('', 'end', values=metadata_list)
        self.update_idletasks()
        # Call the sort function
        self.update_sort()


    def go_to_processing_page(self):
        from ProcessingPage import ProcessingPage
        selected_item = self.tree.selection()
        if len(selected_item) == 1:
            self.master.selected_exp = self.tree.set(selected_item, "c1")
            self.master.basement_name_dynamic = self.tree.set(selected_item, "c2")
            self.master.experiment_path_dynamic = f'{self.master.repository_path_dynamic}/{self.master.selected_exp}'
            self.master.processed_video_path_dynamic = f'{self.master.experiment_path_dynamic}/Processed_Video'
            self.master.exp_list = []
            self.tree.delete(*self.tree.get_children())
            self.master.show_frame(ProcessingPage)
            self.update_sort()
        else:
            messagebox.showwarning("Warning", "Please select one Experiment to process.")


    def back_to_continue_page(self):
        from ContinuePage import ContinuePage
        self.master.exp_list = []
        self.tree.delete(*self.tree.get_children())
        self.update_sort()
        self.master.show_frame(ContinuePage)