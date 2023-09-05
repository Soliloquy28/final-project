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
        # 选择较小的比例，这样视频就不会超出屏幕尺寸
        scale_ratio = min(width_ratio, height_ratio)
        fps_source = cap.get(cv.CAP_PROP_FPS)

        # Read first frame
        success, frame = cap.read()
        # quit if unable to read the video file
        if not success:
            sys.exit(1)

        frame = cv.resize(frame, None, fx=scale_ratio, fy=scale_ratio)
        height, width = frame.shape[:2]

        # 先进行去噪
        frame = cv.GaussianBlur(frame, (3, 3), 0)
        # # 然后提高对比度
        alpha = 1  # Contrast control (1.0-3.0)
        beta = 0  # Brightness control (0-100)
        frame = cv.convertScaleAbs(frame, alpha=alpha, beta=beta)
        # 最后进行锐化
        kernel_sharpening = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        frame = cv.filter2D(frame, -1, kernel_sharpening)

        p_list = []
        # 四个标记点
        dst_point = Global.multiple_size  # 输出变换图像长宽
        frame_copy = frame.copy()
        # frame_copy = cv.resize(frame_copy, None, fx=scale_ratio, fy=scale_ratio)
        cv.namedWindow("Source Video", cv.WINDOW_AUTOSIZE)
        cv.imshow("Source Video", frame)

        # 计算中心点: 计算四个点的均值
        # 基于中心点对四个点排序:
        # 与中心点相对的四个点可以通过其与中心点的角度进行排序。角度可以使用atan2函数计算。
        # math.atan2 * 180 / pi % 360 算绝对角度
        # 右上绝对角度最小，然后是左上，左下，右下
        # sorted按point和中心点centroid的绝对角度从小到大排序
        # 最后抽出来的顺序是[1, 2, 3, 0]
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
                    selectROI_and_start_tracking(dst)  # 开始选择ROI并进行追踪
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
                    # pts1 = sort_points(p_list)
                    pts2 = np.float32([[0, 0], [0, dst_point[1]], [dst_point[0], dst_point[1]], [dst_point[0], 0]])
                    dst = cv.warpPerspective(frame, cv.getPerspectiveTransform(self.pts1, pts2), dst_point)

                    # 先进行去噪
                    dst = cv.GaussianBlur(dst, (3, 3), 0)

                    # # 然后提高对比度
                    alpha = 1  # Contrast control (1.0-3.0)
                    beta = 0  # Brightness control (0-100)
                    dst = cv.convertScaleAbs(dst, alpha=alpha, beta=beta)

                    # 最后进行锐化
                    kernel_sharpening = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                    dst = cv.filter2D(dst, -1, kernel_sharpening)

                    success1, boxes = multiTracker.update(dst)
                    distance_spot_coordinate = []
                    if success1:
                        for i, newbox in enumerate(boxes):
                            p1 = (int(newbox[0]), int(newbox[1]))  # 左上角坐标
                            p2 = (int(newbox[0] + newbox[2]), int(newbox[1] + newbox[3]))  # 右下角坐标
                            cv.rectangle(dst, p1, p2, colors[i], 2, 1)
                            dx = int(newbox[0] + newbox[2] / 2)
                            dy = int(newbox[1] + newbox[3] / 2)
                            dsc = (dx, dy)
                            distance_spot_coordinate.append(dsc)

                            # 新的代码：根据索引添加到正确的列表中
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
                            p1 = (int(newbox[0]), int(newbox[1]))  # 左上角坐标
                            distance_spot_coordinate.append((0, 0))
                            # 新的代码：根据索引添加到正确的列表中
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

                            # cv.putText(dst, "Press ESC to exit", (200, 1200), cv.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 2)
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

            # 读取 JSON 文件
            with open(f'{repo_path}/{current_exp_file}/metadata.json', 'r') as file:
                data = json.load(file)
            if any(os.scandir(processed_video_path)):
                # 对数据进行更新
                data['processedvideo'] = f'{processed_video_path}/{video_name}'  # 取决于你的JSON文件的结构和你需要更新的内容
                data['status'] = "Processed"
                data['distancelist'] = list(dyadic_distance_list)
                data['object1coordinatelist'] = object1_coordinates
                data['object2coordinatelist'] = object2_coordinates
                data['totalframe'] = len(data['object1coordinatelist'])
                data['boxes'] = len(bboxes)
                data['trackingmethod'] = "Multiple object tracking"

                # 将更新后的数据写回文件
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
                # 读取 JSON 文件
                with open(f'{self.master.experiment_path_dynamic}/metadata.json', 'r') as file:
                    data = json.load(file)
                # 对数据进行更新
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
                # 将更新后的数据写回文件
                with open(f'{self.master.experiment_path_dynamic}/metadata.json', 'w') as file:
                    json.dump(data, file, indent=4)
                # 删除processed video
                dir = f'{self.master.experiment_path_dynamic}/Processed_Video'
                for files in os.listdir(dir):
                    path = os.path.join(dir, files)
                    os.remove(path)
                # 找到Annotation文件夹下的所有Word文档，无论是 .doc 还是 .docx
                word_files_anno = glob.glob(os.path.join(f'{self.master.experiment_path_dynamic}/Annotation', "*.doc*"))
                for word_file_anno in word_files_anno:
                    # 删除指定的 Word 文档
                    os.remove(word_file_anno)
                # 找到Metrics_Result文件夹下的所有Word文档，无论是 .doc 还是 .docx
                word_files_metrics = glob.glob(
                    os.path.join(f'{self.master.experiment_path_dynamic}/Metrics_Result', "*.doc*"))
                for word_file_metrics in word_files_metrics:
                    # 删除指定的 Word 文档
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
        fps_source = cap.get(cv.CAP_PROP_FPS)

        # Read first frame
        success, frame = cap.read()
        # quit if unable to read the video file
        if not success:
            sys.exit(1)

        # 加载轨道目标检测器
        # 黄色目标物HSV条件: H>=20 and H<=60 and S>100
        # 透视变换图尺寸: [450, 1500]
        # 边界拓展尺寸：[300,100]
        rd = RailDetector(20, 60, 100, Global.blob_size, Global.blob_border_size)

        # 坚持检测两个目标
        bboxes, img = rd.keepDetect(f'{source_video_path}/{video_name}', 2)

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
        writer = cv.VideoWriter(f'{processed_video_path}/{video_name}', apiPreference=0, fourcc=fourcc, fps=17, frameSize=Global.blob_size)

        dyadic_distance_list = []
        object1_coordinates = []
        object2_coordinates = []

        # Process video and track objects
        while cap.isOpened():
            success, frame = cap.read()
            if success:
                # 获取透视变换图
                dst = rd.getPerspectiveImage(frame)

                # 先进行去噪
                dst = cv.GaussianBlur(dst, (3, 3), 0)

                # # 然后提高对比度
                alpha = 1  # Contrast control (1.0-3.0)
                beta = 0  # Brightness control (0-100)
                dst = cv.convertScaleAbs(dst, alpha=alpha, beta=beta)

                # 最后进行锐化
                kernel_sharpening = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
                dst = cv.filter2D(dst, -1, kernel_sharpening)

                success1, boxes = multiTracker.update(dst)
                distance_spot_coordinate = []
                if success1:
                    for i, newbox in enumerate(boxes):
                        p1 = (int(newbox[0]), int(newbox[1]))  # 左上角坐标
                        p2 = (int(newbox[0] + newbox[2]), int(newbox[1] + newbox[3]))  # 右下角坐标
                        cv.rectangle(dst, p1, p2, colors[i], 2, 1)
                        dx = int(newbox[0] + newbox[2] / 2)
                        dy = int(newbox[1] + newbox[3] / 2)
                        dsc = (dx, dy)
                        distance_spot_coordinate.append(dsc)

                        # 新的代码：根据索引添加到正确的列表中
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
                    rsdst=cv.resize(dst,(int(dst.shape[1]*rate),int(dst.shape[0]*rate)))
                    cv.imshow('Perspective Video', rsdst)
                    writer.write(dst)

                    # quit on Esc button
                    if cv.waitKey(1) & 0xFF == 27:  # Esc pressed
                        break
                else:
                    for i, newbox in enumerate(boxes):
                        distance_spot_coordinate.append((0, 0))
                        # 新的代码：根据索引添加到正确的列表中
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

        # 读取 JSON 文件
        with open(f'{repo_path}/{current_exp_file}/metadata.json', 'r') as file:
            data = json.load(file)
        if any(os.scandir(processed_video_path)):
            # 对数据进行更新
            data['processedvideo'] = f'{processed_video_path}/{video_name}'  # 取决于你的JSON文件的结构和你需要更新的内容
            data['status'] = "Processed"
            data['distancelist'] = list(dyadic_distance_list)
            data['object1coordinatelist'] = object1_coordinates
            data['object2coordinatelist'] = object2_coordinates
            data['totalframe'] = len(data['object1coordinatelist'])
            data['boxes'] = len(bboxes)
            data['trackingmethod'] = "Blob tracking"

            # 将更新后的数据写回文件
            with open(f'{repo_path}/{current_exp_file}/metadata.json', 'w') as file:
                json.dump(data, file, indent=4)
        self.master.process_status = data['status']


    def blob_tracking(self):
        if self.master.process_status == "Unprocessed":
            self.blob_tracking_process()
        else:
            choice = messagebox.askyesno("Confirmation", "The source video has been processed, do you want to process again?\nIf you do that, all your annotations and metrics records will be deleted!")
            if choice:
                # 读取 JSON 文件
                with open(f'{self.master.experiment_path_dynamic}/metadata.json', 'r') as file:
                    data = json.load(file)
                # 对数据进行更新
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
                # 将更新后的数据写回文件
                with open(f'{self.master.experiment_path_dynamic}/metadata.json', 'w') as file:
                    json.dump(data, file, indent=4)
                # 删除processed video
                dir = f'{self.master.experiment_path_dynamic}/Processed_Video'
                for files in os.listdir(dir):
                    path = os.path.join(dir, files)
                    os.remove(path)
                # 找到Annotation文件夹下的所有Word文档，无论是 .doc 还是 .docx
                word_files_anno = glob.glob(os.path.join(f'{self.master.experiment_path_dynamic}/Annotation', "*.doc*"))
                for word_file_anno in word_files_anno:
                    # 删除指定的 Word 文档
                    os.remove(word_file_anno)
                # 找到Metrics_Result文件夹下的所有Word文档，无论是 .doc 还是 .docx
                word_files_metrics = glob.glob(
                    os.path.join(f'{self.master.experiment_path_dynamic}/Metrics_Result', "*.doc*"))
                for word_file_metrics in word_files_metrics:
                    # 删除指定的 Word 文档
                    os.remove(word_file_metrics)
                self.blob_tracking_process()