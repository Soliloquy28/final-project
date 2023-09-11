from __future__ import print_function
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, filedialog
import os
import shutil
import json
import datetime


# Upload Page frame class
class UploadPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        directory_path = os.path.abspath(os.getcwd())
        self.master.repository_path_dynamic = f'{directory_path}/Repository'
        self.directory_path = tk.Label(self, text="Working Directory:")
        self.directory_path.place(relx=0.5, rely=0.15, anchor='center')
        self.directory_path_message = tk.Message(self, text=directory_path, width=500)
        self.directory_path_message.place(relx=0.5, rely=0.2, anchor='center')

        self.upload_sort_column = None
        self.upload_sort_direction = False

        self.upload_tree_frame = tk.Frame(self)  # Create a frame for the Treeview and Scrollbar
        self.upload_tree_frame.place(relx=0.5, rely=0.5, anchor='center')

        self.upload_tree = ttk.Treeview(self.upload_tree_frame, columns=("c1", "c2", "c3"), show='headings',
                                 selectmode="extended", height=11)
        self.upload_tree.column("c1", anchor=tk.CENTER, width=100)
        self.upload_tree.heading("c1", text="Experiment", command=lambda _col="c1": self.sortby(_col, 0))
        self.upload_tree.column("c2", anchor=tk.CENTER, width=300)
        self.upload_tree.heading("c2", text="Video Name", command=lambda _col="c2": self.sortby(_col, 0))
        self.upload_tree.column("c3", anchor=tk.CENTER, width=150)
        self.upload_tree.heading("c3", text="Time Created", command=lambda _col="c3": self.sortby(_col, 0))

        self.upload_tree.pack(side=tk.LEFT)
        # Create a vertical scrollbar
        self.upload_tree_vsb = ttk.Scrollbar(self.upload_tree_frame, orient="vertical", command=self.upload_tree.yview)
        self.upload_tree_vsb.pack(side=tk.RIGHT, fill=tk.Y)
        # Configure the treeview to use the scrollbar
        self.upload_tree.configure(yscrollcommand=self.upload_tree_vsb.set)

        self.browse_file_button = tk.Button(self, text="Upload Video(s)", command=self.ask_open_file_name, cursor="hand2")
        self.browse_file_button.place(relx=0.5, rely=0.8, anchor='center')
        self.upload_delete_all_btn = tk.Button(self, text="Delete All", command=self.upload_delete_all, cursor="hand2")
        self.upload_delete_all_btn.place(relx=0.8, rely=0.05, anchor='nw')
        self.delete_button = tk.Button(self, text="Delete Selected File(s)", command=self.delete_file, cursor="hand2")
        self.delete_button.place(relx=0.3, rely=0.9, anchor='center')
        self.choose_button = tk.Button(self, text="Go To Processing Page", command=self.go_to_processing_page, cursor="hand2")
        self.choose_button.place(relx=0.7, rely=0.9, anchor='center')
        self.back_button = tk.Button(self, text="Back", command=self.back_to_mode_page, cursor="hand2")
        self.back_button.place(relx=0.05, rely=0.05, anchor='nw')

        self.master.protocol("WM_DELETE_WINDOW", self.quit)


    def sortby(self, col, descending):
        data = []
        is_num = True
        for child in self.upload_tree.get_children(''):
            data.append((self.upload_tree.set(child, col), child))
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
            # Special handling if it's pure numerical data
            data = sorted(data, key=lambda x: (float(x[0]), x[1]), reverse=descending)
        else:
            # Sort case-insensitively
            data = sorted(data, key=lambda x: (x[0].lower(), x[1]), reverse=descending)
        # Update the sorted data
        for indx, item in enumerate(data):
            self.upload_tree.move(item[1], '', indx)
        self.upload_tree.heading(col, command=lambda _col=col: self.sortby(col, int(not descending)))
        # Save sorting column and direction for future data insertion, to display in the original order
        self.upload_sort_column = col
        self.upload_sort_direction = descending


    def update_sort(self):
        if not self.upload_sort_column:
            self.upload_sort_column = 'c3'
            self.upload_sort_direction = True
        self.sortby(self.upload_sort_column, self.upload_sort_direction)


    def is_num(self, ss):
        try:
            float(ss)
            return True
        except:
            return False


    def go_to_processing_page(self):
        from ProcessingPage import ProcessingPage
        self.master.selected_exp = ""
        selected_item = self.upload_tree.selection()
        if len(selected_item) == 1:
            self.master.selected_new = self.upload_tree.set(selected_item, "c1")
            self.master.basement_name_dynamic = self.upload_tree.set(selected_item, "c2")
            self.master.experiment_path_dynamic = f'{self.master.repository_path_dynamic}/{self.master.selected_new}'
            self.master.processed_video_path_dynamic = f'{self.master.experiment_path_dynamic}/Processed_Video'
            self.master.show_frame(ProcessingPage)
            self.update_sort()
        else:
            messagebox.showwarning("Warning", "Please select one Experiment to process.")


    def ask_open_file_name(self):
        if self.master.selected_file_path == "":
            file_paths = filedialog.askopenfilenames(initialdir='/Volumes/EIPROJECTBU', filetypes=[("MP4 Files", "*.mp4")])
            # Loop over each selected file
            for file_path in file_paths:
                file_name = os.path.basename(file_path)
                if file_path:
                    directory_path = os.path.abspath(os.getcwd())
                    # Create repository if not exists
                    if "Repository" not in os.listdir(directory_path):
                        os.makedirs(f'{directory_path}/Repository')
                    repository_path = f'{directory_path}/Repository'
                    self.master.repository_path_dynamic = repository_path
                    # Calculate identifier
                    identifier = 1
                    exp_list = [dir for dir in os.listdir(repository_path) if dir.startswith("Experiment")]
                    if exp_list:
                        identifier_list = [int(exp.split('_')[-1]) for exp in exp_list if exp.split('_')[-1].isdigit()]
                        identifier_list.sort()
                        identifier = identifier_list[-1] + 1

                    # Create experiment directories
                    exp_name = self.create_experiment(repository_path, identifier)

                    # Copy selected file to source_video directory
                    shutil.copy(file_path, self.source_video_path)

                    # Create and write metadata
                    metadata = self.create_metadata(file_path, file_name, exp_name)
                    with open(f"{self.experiment_path}/metadata.json", "w") as outfile:
                        json.dump(metadata, outfile, indent=4)
                    with open(f'{self.experiment_path}/metadata.json', 'r') as file:
                        data = json.load(file)
                    experiment = data["experiment"]
                    video_name = data["videoname"]
                    time_created = data["timecreate"]
                    status = data["status"]
                    metadata_list = [experiment, video_name, time_created, status]
                    self.upload_tree.insert('', 'end', values=metadata_list)
        else:
            messagebox.showwarning("Warning", "Please delete the uploaded file first.")


    def upload_delete_all(self):
        choice = messagebox.askyesno("Confirmation", "Are you sure you want to delete all your experiment(s)?")
        if choice:
            directory_path = os.path.abspath(os.getcwd())
            repository_path = f'{directory_path}/Repository'
            for item in self.upload_tree.get_children():
                item_values = self.upload_tree.item(item, "values")
                experiment_selected = item_values[0]
                # Delete the experiment folder
                experiment_path = f'{repository_path}/{experiment_selected}'
                if experiment_path and os.path.exists(experiment_path):
                    shutil.rmtree(experiment_path)
                # Clear the treeview
                self.upload_tree.delete(item)
            self.update_sort()



    def delete_file(self):
        selected_item = self.upload_tree.selection()
        # If none are selected and deleted directly
        if len(selected_item) > 0:
            choice = messagebox.askyesno("Confirmation", "Are you sure you want to delete the uploaded file?")
            if choice:
                directory_path = os.path.abspath(os.getcwd())
                repository_path = f'{directory_path}/Repository'
                for item_id in selected_item:
                    item_values = self.upload_tree.item(item_id, "values")
                    experiment_selected = item_values[0]
                    # Delete the experiment folder
                    experiment_path = f'{repository_path}/{experiment_selected}'
                    if experiment_path and os.path.exists(experiment_path):
                        shutil.rmtree(experiment_path)
                    # Delete from treeview
                    self.upload_tree.delete(item_id)
                    self.update_sort()
                # Reset file path label and stored file path
                self.experiment_path = ""
                self.master.selected_file_path = ""
                self.master.repository_path_dynamic = ""
                self.master.experiment_path_dynamic = ""
                self.master.source_video_path_dynamic = ""
                self.master.processed_video_path_dynamic = ""
        else:
            messagebox.showwarning("Warning", "Please select at least one experiment.")


    # Initialize experiment folder
    def create_experiment(self, repository_path, identifier):
        exp_dir = f'{repository_path}/Experiment_{identifier}'
        os.makedirs(exp_dir)
        os.makedirs(f'{exp_dir}/Source_Video')
        os.makedirs(f'{exp_dir}/Processed_Video')
        os.makedirs(f'{exp_dir}/Annotation')
        os.makedirs(f'{exp_dir}/Metrics_Result')
        self.experiment_path = exp_dir
        self.master.experiment_path_dynamic = exp_dir
        self.source_video_path = f'{exp_dir}/Source_Video'
        self.master.source_video_path_dynamic = self.source_video_path
        self.processed_video_path = f'{exp_dir}/Processed_Video'
        self.master.processed_video_path_dynamic = self.processed_video_path
        self.metrics_path = f'{exp_dir}/Metrics_Result'
        self.annotation_path = f'{exp_dir}/Annotation'

        return f"Experiment_{identifier}"


    # Initialize metadata.json file
    def create_metadata(self, source_video_path, source_video_name, experiment_name):
        # File creation timestamp in float
        c_time = os.path.getctime(self.experiment_path)
        # Convert creation timestamp into DateTime object
        dt_c = datetime.datetime.fromtimestamp(c_time)

        # Author
        full_name = self.master.username.get().strip()

        # Status
        status = "Unprocessed"

        metadata = {
            "experiment": experiment_name,
            "sourcevideo": source_video_path,
            "processedvideo": "",
            "videoname": source_video_name,
            "totalframe": 0,
            "distancelist": "",
            "object1coordinatelist": "",
            "object2coordinatelist": "",
            "boxes": 0,
            "prox": [],
            "csem": [],
            "cs": [],
            "rv": [],
            "di": [],
            "annotation": [],
            "timecreate": dt_c.strftime("%Y-%m-%d %H:%M:%S"),
            "author": full_name,
            "status": status,
        }

        return metadata


    def back_to_mode_page(self):
        from ModePage import ModePage
        self.master.show_frame(ModePage)