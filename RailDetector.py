import cv2 as cv
import numpy as np


# Get the distance between two points
def get_distance(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)
    distance = np.linalg.norm(p1 - p2)
    return distance


# Get the list of external contours
def get_contours(binary):
    contours, hierarchy = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contours = np.array(contours, dtype=object)
    return contours


# Get the binary image with the largest area
def get_max_area_binary(binary):
    max_binary = np.zeros_like(binary)
    contours = get_contours(binary)
    areas = [cv.contourArea(cnt) for cnt in contours]
    cv.drawContours(max_binary, contours, np.argmax(areas), 1, -1)
    return max_binary


# Get the coordinates of the four vertices of the foreground region in
# the binary image (top-left, top-right, bottom-right, bottom-left)
def get_four_points(binary):
    contours = get_contours(binary)
    points = np.concatenate(contours)[:, 0, :]
    rb = points[np.argmax(points[:, 0] + points[:, 1])]
    lt = points[np.argmin(points[:, 0] + points[:, 1])]
    rt = points[np.argmax(points[:, 0] - points[:, 1])]
    lb = points[np.argmin(points[:, 0] - points[:, 1])]
    four_points = np.array([lt, rt, rb, lb])
    return four_points


# Get the perspective transformation matrix
def get_perspective_transform(src_points, dst_points):
    src_points = np.float32(src_points)
    dst_points = np.float32(dst_points)
    transform = cv.getPerspectiveTransform(src_points, dst_points)
    return transform


class RailDetector:
    def __init__(self, min_h, max_h, min_s, size, border_size=None, min_distance_radius_scale=2):
        self.key_infos = []
        self.key_points = []
        self.bboxes = []
        self.transform = None
        self.back_color = None
        self.min_h = min_h
        self.max_h = max_h
        self.min_s = min_s
        self.size = size
        self.border_size = border_size
        self.min_distance_radius_scale = min_distance_radius_scale
        self.params = cv.SimpleBlobDetector_Params()
        # Get the Blob detector
        self.detector = cv.SimpleBlobDetector_create(self.params)

    # Continue detection until the detection count reaches the target count
    def keep_detect(self, video_path, count):
        _cap = cv.VideoCapture(video_path)
        wimg = None
        while True:
            success, frame = _cap.read()
            if success == False:
                break
            try:
                _, wimg = self.detect(frame)
            except:
                pass
            if len(self.key_infos) == count:
                break
        _cap.release()
        return self.bboxes, wimg

    def detect(self, img):
        wimg = self.get_perspective_image(img)
        # Get the HSV image
        hsv = cv.cvtColor(wimg, cv.COLOR_BGR2HSV)
        gray = 255 - cv.cvtColor(wimg, cv.COLOR_BGR2GRAY)
        key_points = self.detector.detect(gray)
        for kp in key_points:
            x, y = np.array(kp.pt, dtype=np.int32)
            r = int(kp.size // 2)
            rhsv = hsv[y - r:y + r, x - r:x + r]
            mrh = np.mean(rhsv[:, :, 0])
            mrs = np.mean(rhsv[:, :, 1])
            if mrh >= self.min_h and mrh <= self.max_h and mrs > self.min_s:
                self.add_key_info([x, y, r], kp)
        return self.bboxes, wimg

    # Get the perspective transformation image
    def get_perspective_image(self, img):
        if self.transform is None:
            self.transform = self.auto_get_perspective_transform(img)
        rstimg = cv.warpPerspective(img, self.transform, tuple(self.size))
        if self.border_size is not None:
            rstimg = self.get_border_image(rstimg, self.border_size)
        return rstimg

    # Get the border extension image
    def get_border_image(self, img, size):
        border_img = cv.copyMakeBorder(img, size[1] // 2, size[1] // 2, size[0] // 2, size[0] // 2,
                                      cv.BORDER_CONSTANT, value=self.back_color)
        return border_img

    # Visualize Blob detection key points
    def visualize(self, img):
        vimg = cv.drawKeypoints(img, self.key_points, np.array([]), (0, 0, 255),
                                cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        return vimg

    # Add key information
    def add_key_info(self, key_info, kp):
        x, y, r = key_info
        valid = True
        for info in self.key_infos:
            x2, y2, r2 = info
            distance = get_distance([x, y], [x2, y2])
            if distance / np.max([r, r2]) < self.min_distance_radius_scale:
                valid = False
                break

        if len(self.key_infos) == 0 or valid:
            self.key_infos.append(key_info)
            self.key_points.append(kp)
            self.bboxes.append([x - r, y - r, 2 * r, 2 * r])

    # Get the track binary image
    def get_rail_binary(self, img):
        # Get the grayscale image
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        _, binary = cv.threshold(gray, 0, 1, cv.THRESH_OTSU)
        max_binary = get_max_area_binary(binary)
        self.back_color = np.round(np.mean(img[(max_binary > 0) & (binary > 0)], axis=0)).astype(np.uint8).tolist()
        # Get the binary image of the rail area
        rail_area_binary = np.uint8((max_binary > 0) & (binary == 0))
        # Get the list of contours in the rail area binary image
        contours = get_contours(rail_area_binary)
        # Get the list of perimeters of contours
        lengths = np.array([cv.arcLength(cnt, True) for cnt in contours])
        # Get the list of contours with perimeters greater than half of the maximum perimeter,
        # which is the rail contour list, mainly to filter out non-rail contours
        contours = contours[lengths > np.max(lengths) // 2]
        rail_binary = np.zeros_like(rail_area_binary)
        cv.drawContours(rail_binary, contours, -1, 1, -1)
        return rail_binary

    # Automatically obtain the perspective transformation matrix
    def auto_get_perspective_transform(self, img):
        rail_binary = self.get_rail_binary(img)
        src_points = get_four_points(rail_binary)
        dst_points = [[0, 0], [self.size[0], 0], [self.size[0], self.size[1]], [0, self.size[1]]]
        transform = get_perspective_transform(src_points, dst_points)
        return transform
