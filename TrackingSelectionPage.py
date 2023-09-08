from __future__ import print_function
import tkinter as tk
from tkinter import messagebox
import os
import json
import math
import sys
from random import randint
import glob
from RailDetector import *
import Global




class TrackingSelectionPage(tk.Frame):
    def __init__(self, master):
        tk.Frame.__init__(self, master)
        self.back_button = tk.Button(self, text="Back", command=self.back_to_process_page, cursor="hand2")
        self.back_button.place(relx=0.05, rely=0.05, anchor='nw')
        self.manual_label = tk.Label(self, text="Manual Selection:")
        self.manual_label.place(relx=0.5, rely=0.25, anchor='center')
        self.manual_btn = tk.Button(self, text="Multiple Object Tracking", command=self.multiple_tracking)
        self.manual_btn.place(relx=0.5, rely=0.35, anchor='center')
        self.automatic_label = tk.Label(self, text="Automatic Selection:")
        self.automatic_label.place(relx=0.5, rely=0.5, anchor='center')
        self.automatic_btn = tk.Button(self, text="Blob Tracking", command=self.blob_tracking)
        self.automatic_btn.place(relx=0.5, rely=0.6, anchor='center')
        self.multiple_tracked = False
        self.blob_tracked = False

    def back_to_process_page(self):
        from ProcessingPage import ProcessingPage
        self.master.show_frame(ProcessingPage)

    def multiple_tracking_process(self):
        directory_path = os.path.abspath(os.getcwd())
        repo_path = f'{directory_path}/Repository'
        if self.master.selected_exp == "":
            current_exp_file = self.master.selected_new
        else:
            current_exp_file = self.master.selected_exp
        source_video_path = f'{repo_path}/{current_exp_file}/Source_Video'
        processed_video_path = f'{repo_path}/{current_exp_file}/Processed_Video'

        for root, dir, file in os.walk(source_video_path):
            video_name = file[0]

        # Create a video capture object to read videos
        cap = cv.VideoCapture(f'{source_video_path}/{video_name}')
        video_width = cap.get(cv.CAP_PROP_FRAME_WIDTH)
        video_height = cap.get(cv.CAP_PROP_FRAME_HEIGHT)
        width_ratio = Global.screen_width / video_width
        height_ratio = Global.screen_height / video_height
        # Choose a smaller scale to ensure the video does not exceed the screen size
        scale_ratio = min(width_ratio, height_ratio)

        # Read first frame
        success, frame = cap.read()
        # quit if unable to read the video file
        if not success:
            sys.exit(1)
        frame = cv.resize(frame, None, fx=scale_ratio, fy=scale_ratio)

        # Begin with denoising
        frame = cv.GaussianBlur(frame, (3, 3), 0)
        # Then increase contrast
        alpha = 1  # Contrast control (1.0-3.0)
        beta = 0  # Brightness control (0-100)
        frame = cv.convertScaleAbs(frame, alpha=alpha, beta=beta)
        # Finally, perform sharpening
        kernel_sharpening = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        frame = cv.filter2D(frame, -1, kernel_sharpening)

        # Four marked points
        p_list = []
        dst_point = Global.multiple_size  # Output the dimensions of the transformed image
        frame_copy = frame.copy()
        cv.namedWindow("Source Video", cv.WINDOW_AUTOSIZE)
        cv.imshow("Source Video", frame)

        # Calculate the center point: Calculate the mean of the four points
        # Sort the four points based on the center point:
        # The four points relative to the center point can be sorted by their angles with respect to the center point.
        # Angles can be calculated using the atan2 function.
        # math.atan2 * 180 / pi % 360 calculates the absolute angle
        # The absolute angle is smallest for the bottom-right, followed by bottom-left, top-left, and top-right
        # Sorting with sorted based on the absolute angle between each point and the centroid
        # The final order obtained is [2, 1, 0, 3]
        def sort_points(points):
            # Calculate centroid
            centroid_x = sum([p[0] for p in points]) / 4
            centroid_y = sum([p[1] for p in points]) / 4

            # Calculate angles
            angles = []
            for p in points:
                dx = p[0] - centroid_x
                dy = p[1] - centroid_y
                angle = (math.atan2(dy, dx) * (180 / math.pi)) % 360
                angles.append(angle)

            # Zip points with their respective angles for sorting
            points_with_angles = list(zip(points, angles))

            # Sort points based on angle with centroid
            sorted_points_with_angles = sorted(points_with_angles, key=lambda x: x[1])
            sorted_points = [p[0] for p in sorted_points_with_angles]

            # Return in the order: top-left, bottom-left, bottom-right, top-right
            return [sorted_points[i] for i in [2, 1, 0, 3]]

        def capture_event(event, x, y, flags, params):
            if event == cv.EVENT_LBUTTONDOWN:
                cv.circle(frame, (x, y), 10, (0, 0, 255), -1)
                cv.imshow("Source Video", frame)
                p_list.append([x, y])
                if len(p_list) == 4:
                    self.pts1 = sort_points(p_list)
                    self.pts1 = np.float32(self.pts1)
                    pts2 = np.float32([[0, 0], [0, dst_point[1]], [dst_point[0], dst_point[1]], [dst_point[0], 0]])
                    dst = cv.warpPerspective(frame_copy, cv.getPerspectiveTransform(self.pts1, pts2), dst_point)
                    cv.namedWindow("Perspective", cv.WINDOW_AUTOSIZE)
                    rate = Global.screen_height/dst.shape[0]
                    rsdst=cv.resize(dst,(int(dst.shape[1]*rate),int(dst.shape[0]*rate)))
                    cv.imshow("Perspective", rsdst)
                    cv.destroyWindow("Source Video")
                    # Begin selecting the ROI and tracking
                    selectROI_and_start_tracking(dst)
            elif event == cv.EVENT_RBUTTONDOWN:
                # right click is for removing points
                if p_list:
                    # find the nearest point within a certain threshold and remove it
                    distances = np.sqrt(np.sum((np.array(p_list) - np.array([x, y])) ** 2, axis=1))
                    if np.min(distances) < 80:  # the threshold is 80 pixels
                        del p_list[np.argmin(distances)]
                        frame[:] = frame_copy[:]  # restore the original frame
                        for point in p_list:
                            cv.circle(frame, tuple(point), 10, (0, 0, 255), -1)  # redraw remaining points
                        cv.imshow("Source Video", frame)

        def selectROI_and_start_tracking(img):
            # Select boxes
            bboxes = []
            colors = []

            while True:
                # draw bounding boxes over objects
                rate = Global.screen_height/img.shape[0]
                rsimg=cv.resize(img,(int(img.shape[1]*rate),int(img.shape[0]*rate)))
                bbox = cv.selectROI('Perspective', rsimg)
                bbox = tuple((np.array(bbox)/rate).tolist())
                if bbox == (0, 0, 0, 0):
                    pass
                else:
                    bboxes.append(bbox)
                colors.append((randint(0, 255), randint(0, 255), randint(0, 255)))
                k = cv.waitKey(0) & 0xFF
                if (k == 113):  # q is pressed
                    cv.destroyWindow("Perspective")
                    break

            # Specify the tracker type
            trackerType = "CSRT"

            self.master.boxes_length = len(bboxes)

            # Create MultiTracker object
            multiTracker = cv.legacy.MultiTracker_create()

            # Initialize MultiTracker
            for bbox in bboxes:
                multiTracker.add(cv.legacy.TrackerCSRT_create(), img, bbox)

            # we are using mp4v codec for mp4
            fourcc = cv.VideoWriter_fourcc(*'mp4v')
            writer = cv.VideoWriter(f'{processed_video_path}/{video_name}', apiPreference=0, fourcc=fourcc, fps=17, frameSize=Global.multiple_size)

            dyadic_distance_list = []
            object1_coordinates = []
            object2_coordinates = []

            # Process video and track objects
            while cap.isOpened():
                success, frame = cap.read()
                if success:
                    frame = cv.resize(frame, None, fx=scale_ratio, fy=scale_ratio)
                    # transform frame
                    pts2 = np.float32([[0, 0], [0, dst_point[1]], [dst_point[0], dst_point[1]], [dst_point[0], 0]])
                    dst = cv.warpPerspective(frame, cv.getPerspectiveTransform(self.pts1, pts2), dst_point)

                    dst = cv.GaussianBlur(dst, (3, 3), 0)
                    alpha = 1  # Contrast control (1.0-3.0)
                    beta = 0  # Brightness control (0-100)
                    dst = cv.convertScaleAbs(dst, alpha=alpha, beta=beta)
                    kernel_sharpening = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                    dst = cv.filter2D(dst, -1, kernel_sharpening)

                    success1, boxes = multiTracker.update(dst)
                    distance_spot_coordinate = []
                    if success1:
                        for i, newbox in enumerate(boxes):
                            p1 = (int(newbox[0]), int(newbox[1]))  # Top-left coordinates
                            p2 = (int(newbox[0] + newbox[2]), int(newbox[1] + newbox[3]))  # Bottom-right coordinates
                            cv.rectangle(dst, p1, p2, colors[i], 2, 1)
                            dx = int(newbox[0] + newbox[2] / 2)
                            dy = int(newbox[1] + newbox[3] / 2)
                            dsc = (dx, dy)
                            distance_spot_coordinate.append(dsc)

                            # New code: Add to the correct list based on the index
                            if i == 0:
                                object1_coordinates.append(dsc)
                            elif i == 1:
                                object2_coordinates.append(dsc)

                            cv.putText(dst, f"[{dx}, {dy}]", (p1[0] - 110, p1[1] - 10), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                            cv.putText(dst, "Press ESC to exit", (200, 1200), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                        if len(bboxes) == 2:
                            dyadic_distance = round(math.sqrt(
                                ((distance_spot_coordinate[0][0] - distance_spot_coordinate[1][0]) / Global.multiple_width_ratio) ** 2 + ((distance_spot_coordinate[0][1] - distance_spot_coordinate[1][1]) / Global.multiple_height_ratio) ** 2), 2)
                            cv.putText(dst, f"Distance: {dyadic_distance}cm", (150, 60), cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
                            dyadic_distance_list.append(dyadic_distance)
                        else:
                            cv.putText(dst, "Unavailable", (150, 60), cv.FONT_HERSHEY_SIMPLEX, 1.8, (0, 0, 255), 2)

                        # show frame
                        rate = Global.screen_height/dst.shape[0]
                        rsdst=cv.resize(dst,(int(dst.shape[1]*rate),int(dst.shape[0]*rate)))
                        cv.imshow('Perspective Video', rsdst)
                        writer.write(dst)

                        # quit on Esc button
                        if cv.waitKey(1) & 0xFF == 27:  # Esc pressed
                            break
                    else:
                        for i, newbox in enumerate(boxes):
                            p1 = (int(newbox[0]), int(newbox[1]))  # Top-left coordinates
                            distance_spot_coordinate.append((0, 0))
                            if i == 0:
                                object1_coordinates.append((0, 0))
                            elif i == 1:
                                object2_coordinates.append((0, 0))
                            cv.putText(dst, "[0, 0]", (p1[0] - 110, p1[1] - 10), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                            text_x = int(0.1 * dst.shape[1])
                            text_y = int(0.9 * dst.shape[0])
                            font_scale = dst.shape[1] / 1920
                            cv.putText(dst, "Press ESC to exit", (text_x, text_y), cv.FONT_HERSHEY_SIMPLEX, font_scale,
                                       (0, 0, 255), 2)
                        if len(bboxes) == 2:
                            dyadic_distance = 0
                            cv.putText(dst, f"Distance: {dyadic_distance}cm", (150, 60), cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
                            dyadic_distance_list.append(dyadic_distance)
                        else:
                            cv.putText(dst, "Unavailable", (150, 60), cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)

                else:
                    if cv.waitKey(0) & 0xFF == 27:  # Esc pressed quit
                        break

            writer.release()
            cap.release()
            cv.destroyAllWindows()

            with open(f'{repo_path}/{current_exp_file}/metadata.json', 'r') as file:
                data = json.load(file)
            if any(os.scandir(processed_video_path)):
                data['processedvideo'] = f'{processed_video_path}/{video_name}'
                data['status'] = "Processed"
                data['distancelist'] = list(dyadic_distance_list)
                data['object1coordinatelist'] = object1_coordinates
                data['object2coordinatelist'] = object2_coordinates
                data['totalframe'] = len(data['object1coordinatelist'])
                data['boxes'] = len(bboxes)
                data['trackingmethod'] = "Multiple object tracking"

                with open(f'{repo_path}/{current_exp_file}/metadata.json', 'w') as file:
                    json.dump(data, file, indent=4)
            self.master.process_status = data['status']

        cv.setMouseCallback("Source Video", capture_event)


    def multiple_tracking(self):
        if self.master.process_status == "Unprocessed":
            self.multiple_tracking_process()
        else:
            choice = messagebox.askyesno("Confirmation", "The source video has been processed, do you want to process again?\nIf you do that, all your annotations and metrics records will be deleted!")
            if choice:
                with open(f'{self.master.experiment_path_dynamic}/metadata.json', 'r') as file:
                    data = json.load(file)
                self.master.process_status = "Unprocessed"
                data['status'] = "Unprocessed"
                data['totalframe'] = 0
                data['distancelist'] = []
                data['object1coordinatelist'] = []
                data['object2coordinatelist'] = []
                data['prox'] = []
                data['csem'] = []
                data['cs'] = []
                data['rv'] = []
                data['di'] = []
                data['annotation'] = []
                data['boxes'] = 0
                data['trackingmethod'] = ''
                with open(f'{self.master.experiment_path_dynamic}/metadata.json', 'w') as file:
                    json.dump(data, file, indent=4)
                # Delete the processed video
                dir = f'{self.master.experiment_path_dynamic}/Processed_Video'
                for files in os.listdir(dir):
                    path = os.path.join(dir, files)
                    os.remove(path)
                # Find all Word documents in the Annotation folder, whether .doc or .docx
                word_files_anno = glob.glob(os.path.join(f'{self.master.experiment_path_dynamic}/Annotation', "*.doc*"))
                for word_file_anno in word_files_anno:
                    # Delete the specified Word document
                    os.remove(word_file_anno)
                # Find all Word documents in the Metrics_Result folder, whether .doc or .docx
                word_files_metrics = glob.glob(
                    os.path.join(f'{self.master.experiment_path_dynamic}/Metrics_Result', "*.doc*"))
                for word_file_metrics in word_files_metrics:
                    # Delete the specified Word document
                    os.remove(word_file_metrics)
                self.multiple_tracking_process()


    def blob_tracking_process(self):
        directory_path = os.path.abspath(os.getcwd())
        repo_path = f'{directory_path}/Repository'
        if self.master.selected_exp == "":
            current_exp_file = self.master.selected_new
        else:
            current_exp_file = self.master.selected_exp
        source_video_path = f'{repo_path}/{current_exp_file}/Source_Video'
        processed_video_path = f'{repo_path}/{current_exp_file}/Processed_Video'

        for root, dir, file in os.walk(source_video_path):
            video_name = file[0]

        # Create a video capture object to read videos
        cap = cv.VideoCapture(f'{source_video_path}/{video_name}')

        # Read first frame
        success, frame = cap.read()
        # quit if unable to read the video file
        if not success:
            sys.exit(1)

        # Load the rail target detector
        # Yellow target object HSV conditions: H>=20 and H<=60 and S>100
        # Perspective transformation image size: [450, 1500]
        # Boundary extension size: [300, 100]
        rd = RailDetector(20, 60, 100, Global.blob_size, Global.blob_border_size)

        # Persist in detecting two targets
        bboxes, img = rd.keep_detect(f'{source_video_path}/{video_name}', 2)

        # Specify the tracker type
        trackerType = "CSRT"

        self.master.boxes_length = len(bboxes)

        # Create MultiTracker object
        multiTracker = cv.legacy.MultiTracker_create()

        # Initialize MultiTracker
        colors = []
        for bbox in bboxes:
            colors.append((randint(0, 255), randint(0, 255), randint(0, 255)))
            multiTracker.add(cv.legacy.TrackerCSRT_create(), img, bbox)

        # we are using mp4v codec for mp4
        fourcc = cv.VideoWriter_fourcc(*'mp4v')
        writer = cv.VideoWriter(f'{processed_video_path}/{video_name}', apiPreference=0, fourcc=fourcc, fps=17, frameSize=(img.shape[1], img.shape[0]))

        dyadic_distance_list = []
        object1_coordinates = []
        object2_coordinates = []

        # Process video and track objects
        while cap.isOpened():
            success, frame = cap.read()
            if success:
                dst = rd.get_perspective_image(frame)
                dst = cv.GaussianBlur(dst, (3, 3), 0)
                alpha = 1  # Contrast control (1.0-3.0)
                beta = 0  # Brightness control (0-100)
                dst = cv.convertScaleAbs(dst, alpha=alpha, beta=beta)
                kernel_sharpening = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                dst = cv.filter2D(dst, -1, kernel_sharpening)

                success1, boxes = multiTracker.update(dst)
                distance_spot_coordinate = []
                if success1:
                    for i, newbox in enumerate(boxes):
                        p1 = (int(newbox[0]), int(newbox[1]))
                        p2 = (int(newbox[0] + newbox[2]), int(newbox[1] + newbox[3]))
                        cv.rectangle(dst, p1, p2, colors[i], 2, 1)
                        dx = int(newbox[0] + newbox[2] / 2)
                        dy = int(newbox[1] + newbox[3] / 2)
                        dsc = (dx, dy)
                        distance_spot_coordinate.append(dsc)

                        if i == 0:
                            object1_coordinates.append(dsc)
                        elif i == 1:
                            object2_coordinates.append(dsc)
                        cv.putText(dst, f"[{dx}, {dy}]", (p1[0] - 100, p1[1] - 30), cv.FONT_HERSHEY_SIMPLEX,
                                   0.8, (0, 0, 255), 2)
                        cv.putText(dst, "Press ESC to exit", (230, 1400), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                    if len(bboxes) == 2:
                        dyadic_distance = round(math.sqrt(
                            ((distance_spot_coordinate[0][0] - distance_spot_coordinate[1][0]) / Global.blob_width_ratio) ** 2 + ((distance_spot_coordinate[0][1] - distance_spot_coordinate[1][1]) / Global.blob_height_ratio) ** 2), 2)
                        cv.putText(dst, f"Distance: {dyadic_distance}cm", (230, 60), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                        dyadic_distance_list.append(dyadic_distance)
                    else:
                        cv.putText(dst, "Unavailable", (230, 60), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

                    # show frame
                    rate = Global.screen_height/dst.shape[0]
                    rsdst = cv.resize(dst,(int(dst.shape[1]*rate),int(dst.shape[0]*rate)))
                    cv.imshow('Perspective Video', rsdst)
                    writer.write(dst)

                    # quit on Esc button
                    if cv.waitKey(1) & 0xFF == 27:  # Esc pressed
                        break
                else:
                    for i, newbox in enumerate(boxes):
                        distance_spot_coordinate.append((0, 0))
                        if i == 0:
                            object1_coordinates.append((0, 0))
                        elif i == 1:
                            object2_coordinates.append((0, 0))
                        cv.putText(dst, "[0, 0]", (p1[0] - 110, p1[1] - 10), cv.FONT_HERSHEY_SIMPLEX,
                                   1, (0, 0, 255), 2)
                        cv.putText(dst, "Press ESC to exit", (30, 700), cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    if len(bboxes) == 2:
                        dyadic_distance = 0
                        cv.putText(dst, f"Distance: {dyadic_distance}cm", (30, 60), cv.FONT_HERSHEY_SIMPLEX, 1,
                                   (0, 0, 255), 2)
                        dyadic_distance_list.append(dyadic_distance)
                    else:
                        cv.putText(dst, "Unavailable", (30, 60), cv.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            else:
                if cv.waitKey(0) & 0xFF == 27:  # Esc pressed quit
                    break

        writer.release()
        cap.release()
        cv.destroyAllWindows()

        with open(f'{repo_path}/{current_exp_file}/metadata.json', 'r') as file:
            data = json.load(file)
        if any(os.scandir(processed_video_path)):
            data['processedvideo'] = f'{processed_video_path}/{video_name}'
            data['status'] = "Processed"
            data['distancelist'] = list(dyadic_distance_list)
            data['object1coordinatelist'] = object1_coordinates
            data['object2coordinatelist'] = object2_coordinates
            data['totalframe'] = len(data['object1coordinatelist'])
            data['boxes'] = len(bboxes)
            data['trackingmethod'] = "Blob tracking"

            with open(f'{repo_path}/{current_exp_file}/metadata.json', 'w') as file:
                json.dump(data, file, indent=4)
        self.master.process_status = data['status']


    def blob_tracking(self):
        if self.master.process_status == "Unprocessed":
            self.blob_tracking_process()
        else:
            choice = messagebox.askyesno("Confirmation", "The source video has been processed, do you want to process again?\nIf you do that, all your annotations and metrics records will be deleted!")
            if choice:
                with open(f'{self.master.experiment_path_dynamic}/metadata.json', 'r') as file:
                    data = json.load(file)
                self.master.process_status = "Unprocessed"
                data['status'] = "Unprocessed"
                data['totalframe'] = 0
                data['distancelist'] = []
                data['object1coordinatelist'] = []
                data['object2coordinatelist'] = []
                data['prox'] = []
                data['csem'] = []
                data['cs'] = []
                data['rv'] = []
                data['di'] = []
                data['annotation'] = []
                data['boxes'] = 0
                data['trackingmethod'] = ''
                with open(f'{self.master.experiment_path_dynamic}/metadata.json', 'w') as file:
                    json.dump(data, file, indent=4)
                dir = f'{self.master.experiment_path_dynamic}/Processed_Video'
                for files in os.listdir(dir):
                    path = os.path.join(dir, files)
                    os.remove(path)
                word_files_anno = glob.glob(os.path.join(f'{self.master.experiment_path_dynamic}/Annotation', "*.doc*"))
                for word_file_anno in word_files_anno:
                    os.remove(word_file_anno)
                word_files_metrics = glob.glob(
                    os.path.join(f'{self.master.experiment_path_dynamic}/Metrics_Result', "*.doc*"))
                for word_file_metrics in word_files_metrics:
                    os.remove(word_file_metrics)
                self.blob_tracking_process()