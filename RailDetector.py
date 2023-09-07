import cv2 as cv
import numpy as np


# Get the distance between two points
def getDistance(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)
    distance = np.linalg.norm(p1-p2)
    return distance


# Get the list of external contours
def getContours(binary):
    contours, hierarchy = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contours = np.array(contours, dtype=object)
    return contours


# Get the binary image with the largest area
def getMaxAreaBinary(binary):
    maxBinary = np.zeros_like(binary)
    contours = getContours(binary)
    areas = [cv.contourArea(cnt) for cnt in contours]
    cv.drawContours(maxBinary, contours, np.argmax(areas), 1, -1)
    return maxBinary


# Get the coordinates of the four vertices of the foreground region in
# the binary image (top-left, top-right, bottom-right, bottom-left)
def getQuadrilateralPeakPoints(binary):
    contours = getContours(binary)
    points = np.concatenate(contours)[:, 0, :]
    rb = points[np.argmax(points[:, 0]+points[:, 1])]
    lt = points[np.argmin(points[:, 0]+points[:, 1])]
    rt = points[np.argmax(points[:, 0]-points[:, 1])]
    lb = points[np.argmin(points[:, 0]-points[:, 1])]
    peakPoints = np.array([lt, rt, rb, lb])
    return peakPoints


# Get the perspective transformation matrix
def getPerspectiveTransform(srcPoints, dstPoints):
    srcPoints = np.float32(srcPoints)
    dstPoints = np.float32(dstPoints)
    transform = cv.getPerspectiveTransform(srcPoints, dstPoints)
    return transform


class RailDetector:
    def __init__(self, minH, maxH, minS, size, borderSize=None, minDistanceRadiusScale=2):
        self.keyinfos = []
        self.keypoints = []
        self.bboxes = []
        self.transform = None
        self.backColor = None
        self.minH = minH
        self.maxH = maxH
        self.minS = minS
        self.size = size
        self.borderSize = borderSize
        self.minDistanceRadiusScale = minDistanceRadiusScale
        self.params = cv.SimpleBlobDetector_Params()
        # Get the Blob detector
        self.detector = cv.SimpleBlobDetector_create(self.params)


    # Continue detection until the detection count reaches the target count
    def keepDetect(self, videoPath, count):
        _cap = cv.VideoCapture(videoPath)
        wimg = None
        while True:
            success, frame = _cap.read()
            if success == False:
                break
            try:
                _, wimg = self.detect(frame)
            except:
                pass
            if len(self.keyinfos) == count:
                break
        _cap.release()
        return self.bboxes, wimg


    def detect(self, img):
        wimg = self.getPerspectiveImage(img)
        # Get the HSV image
        hsv = cv.cvtColor(wimg, cv.COLOR_BGR2HSV)
        gray = 255 - cv.cvtColor(wimg, cv.COLOR_BGR2GRAY)
        keypoints = self.detector.detect(gray)
        for kp in keypoints:
            x,y = np.array(kp.pt, dtype=np.int32)
            r = int(kp.size // 2)
            rhsv = hsv[y-r:y+r, x-r:x+r]
            mrh = np.mean(rhsv[:, :, 0])
            mrs = np.mean(rhsv[:, :, 1])
            if mrh >= self.minH and mrh <= self.maxH and mrs > self.minS:
                self.addKeyinfo([x, y, r], kp)
        return self.bboxes, wimg


    # Get the perspective transformation image
    def getPerspectiveImage(self, img):
        if self.transform is None:
            self.transform = self.autoGetPerspectiveTransform(img)
        rstimg = cv.warpPerspective(img, self.transform, tuple(self.size))
        if self.borderSize is not None:
            rstimg = self.getBorderImage(rstimg, self.borderSize)
        return rstimg


    # Get the border extension image
    def getBorderImage(self, img, size):
        borderImg = cv.copyMakeBorder(img, size[1] // 2, size[1] // 2,size[0] // 2, size[0] // 2,
                                               cv.BORDER_CONSTANT, value=self.backColor)
        return borderImg


    # Visualize Blob detection key points
    def visualize(self, img):
        vimg = cv.drawKeypoints(img, self.keypoints, np.array([]), (0, 0, 255), cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        return vimg


    # Add key information
    def addKeyinfo(self, keyinfo, kp):
        x, y, r = keyinfo
        valid = True
        for info in self.keyinfos:
            x2, y2, r2 = info
            distance = getDistance([x, y], [x2, y2])
            if distance / np.max([r, r2]) < self.minDistanceRadiusScale:
                valid = False
                break

        if len(self.keyinfos) == 0 or valid:
            self.keyinfos.append(keyinfo)
            self.keypoints.append(kp)
            self.bboxes.append([x-r, y-r, 2*r, 2*r])


    # Get the track binary image
    def getRailBinary(self, img):
        # Get the grayscale image
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        _, binary = cv.threshold(gray, 0, 1, cv.THRESH_OTSU)
        maxBinary = getMaxAreaBinary(binary)
        self.backColor = np.round(np.mean(img[(maxBinary > 0) & (binary > 0)], axis=0)).astype(np.uint8).tolist()
        # Get the binary image of the rail area
        railAreaBinary = np.uint8((maxBinary > 0) & (binary == 0))
        # Get the list of contours in the rail area binary image
        contours = getContours(railAreaBinary)
        # Get the list of perimeters of contours
        lengths = np.array([cv.arcLength(cnt, True) for cnt in contours])
        # Get the list of contours with perimeters greater than half of the maximum perimeter,
        # which is the rail contour list, mainly to filter out non-rail contours
        contours = contours[lengths > np.max(lengths) // 2]
        railBinary = np.zeros_like(railAreaBinary)
        cv.drawContours(railBinary, contours, -1, 1, -1)
        return railBinary


    # Automatically obtain the perspective transformation matrix
    def autoGetPerspectiveTransform(self, img):
        railBinary = self.getRailBinary(img)
        srcPoints = getQuadrilateralPeakPoints(railBinary)
        dstPoints = [[0, 0], [self.size[0], 0], [self.size[0], self.size[1]], [0, self.size[1]]]
        transform = getPerspectiveTransform(srcPoints, dstPoints)
        return transform