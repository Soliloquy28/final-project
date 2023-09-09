from __future__ import print_function
import tkinter as tk
import os


class Platform(tk.Tk):
    def __init__(self):
        super().__init__()

        self.resizable(False, False)
        self.title('Video Processing Platform')

        # Some global variables
        self.username = tk.StringVar()
        self.continue_username = tk.StringVar()
        self.selected_file_path = ""
        self.selected_exp = tk.StringVar()
        self.selected_new = tk.StringVar()
        self.exp_list = []
        self.process_status = ""
        self.repository_path_dynamic = ""
        self.experiment_path_dynamic = ""
        self.source_video_path_dynamic = ""
        self.processed_video_path_dynamic = ""
        self.basement_name_dynamic = ""
        self.continue_author_list = []
        self.proximity_threshold = tk.StringVar()
        self.csem_threshold = tk.StringVar()
        self.total_frame = tk.StringVar()
        self.frame_enter_value = tk.StringVar()
        self.thread_running = True
        self.boxes_length = 0

        # When closing the main window, the program quits automatically
        self.protocol("WM_DELETE_WINDOW", self.on_quit)

        from LoginPage import LoginPage
        from ModePage import ModePage
        from UploadPage import UploadPage
        from ContinuePage import ContinuePage
        from ExperimentPage import ExperimentPage
        from ProcessingPage import ProcessingPage
        from MetricsSelectionPage import MetricsSelectionPage
        from TrackingSelectionPage import TrackingSelectionPage

        # Switch between different page frames
        # The code from `self.frames = {}` to `frame.tkraise()` is not an original work
        # by the developer but rather comes from the following webpage.
        # https://www.javatpoint.com/tkinter-application-to-switch-between-different-page-frames-in-python
        self.frames = {}
        for F in (LoginPage, ModePage, UploadPage, ContinuePage, ExperimentPage,
                  ProcessingPage, MetricsSelectionPage, TrackingSelectionPage):
            frame = F(self)
            frame.grid(row=0, column=0, sticky="nsew")
            frame.grid_rowconfigure(0, weight=1, minsize=400)
            frame.grid_columnconfigure(0, weight=1, minsize=600)
            self.frames[F] = frame
        self.show_frame(LoginPage)

    # Page frame updates once shift
    def show_frame(self, page):
        from ModePage import ModePage
        from UploadPage import UploadPage
        from ContinuePage import ContinuePage
        from ExperimentPage import ExperimentPage
        from ProcessingPage import ProcessingPage
        frame = self.frames[page]
        if page == ModePage:
            frame.update_username()
        if page == UploadPage:
            frame.update_upload_treeview()
        if page == ContinuePage:
            frame.update_available()
        if page == ExperimentPage:
            frame.update_username_and_list()
        if page == ProcessingPage:
            frame.update_process_status()
        frame.tkraise()

    # Quit the platform
    def on_quit(self):
        os._exit(0)


