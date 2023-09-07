import cv2 as cv
import numpy as np

'''
Get the distance between two points
@param p1: Point 1
@param p2: Point 2
@return distance: Distance between two points
'''
def getDistance(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)
    distance = np.linalg.norm(p1-p2)
    return distance

'''
Get the list of external contours
@param binary: Binary image
@return contours: List of external contours
'''
def getContours(binary):
    contours, hierarchy = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contours = np.array(contours, dtype=object)
    return contours

'''
Get the binary image with the largest area
@param binary: Binary image
@return maxBinary: Binary image with the largest area
'''
def getMaxAreaBinary(binary):
    maxBinary = np.zeros_like(binary)
    contours = getContours(binary)
    areas = [cv.contourArea(cnt) for cnt in contours]
    cv.drawContours(maxBinary, contours, np.argmax(areas), 1, -1)
    return maxBinary

'''
Get the coordinates of the four vertices of the foreground region in the binary image (top-left, top-right, bottom-right, bottom-left)
@param binary: Binary image
@return peakPoints: Coordinates of the four vertices of the foreground region in the binary image (top-left, top-right, bottom-right, bottom-left)
'''
def getQuadrilateralPeakPoints(binary):
    contours = getContours(binary)
    points = np.concatenate(contours)[:, 0, :]
    rb = points[np.argmax(points[:, 0]+points[:, 1])]
    lt = points[np.argmin(points[:, 0]+points[:, 1])]
    rt = points[np.argmax(points[:, 0]-points[:, 1])]
    lb = points[np.argmin(points[:, 0]-points[:, 1])]
    peakPoints = np.array([lt, rt, rb, lb])
    return peakPoints

'''
Get the perspective transformation matrix
@param srcPoints: List of source coordinates
@param dstPoints: List of destination coordinates
@return transform: Perspective transformation matrix
'''
def getPerspectiveTransform(srcPoints, dstPoints):
    srcPoints = np.float32(srcPoints)
    dstPoints = np.float32(dstPoints)
    transform = cv.getPerspectiveTransform(srcPoints, dstPoints)
    return transform

# 轨道目标检测器
class RailDetector:
    '''
    Constructor
    @param minH: Minimum hue
    @param maxH: Maximum hue
    @param minS: Minimum saturation
    @param size: Perspective transformation image size
    @param borderSize: Border extension size
    @param minDistanceRadiusScale: Minimum target distance radius multiple, touching targets are 2
    '''
    def __init__(self, minH, maxH, minS, size, borderSize=None, minDistanceRadiusScale=2):
        # Initialize the key information list
        self.keyinfos = []
        # Initialize the key point information list
        self.keypoints = []
        # Initialize the key bbox list
        self.bboxes = []
        # Initialize the perspective transformation matrix as empty
        self.transform = None
        # Initialize the background color as empty
        self.backColor = None
        # Initialize the minimum hue
        self.minH = minH
        # Initialize the maximum hue
        self.maxH = maxH
        # Initialize the minimum saturation
        self.minS = minS
        # Initialize the perspective transformation image size
        self.size = size
        # Initialize the border extension size
        self.borderSize = borderSize
        # Initialize the minimum target distance radius multiple
        self.minDistanceRadiusScale = minDistanceRadiusScale
        # Get the Blob detector parameter list
        self.params = cv.SimpleBlobDetector_Params()
        # Get the Blob detector
        self.detector = cv.SimpleBlobDetector_create(self.params)

    '''
    Continue detection until the detection count reaches the target count
    @param videoPath: Video path
    @param count: Target count
    @return self.bboxes: List of key bboxes
    @return wimg: Perspective transformation image
    '''
    def keepDetect(self, videoPath, count):
        # Load the video reader
        _cap = cv.VideoCapture(videoPath)
        # Initialize the perspective transformation image
        wimg = None
        # Loop for detection in each frame until the detection count reaches the target count
        while True:
            # Read the next frame
            success, frame = _cap.read()
            # If reading is successful
            if success == False:
                break
            try:
                # Perform target detection and return the perspective transformation image
                _, wimg = self.detect(frame)
            except:
                pass
            # If the length of the key information list equals the target count, exit detection
            if len(self.keyinfos) == count:
                break
        # Release the video reader
        _cap.release()
        return self.bboxes, wimg

    '''
    Target detection
    @param img: Image
    @return self.bboxes: List of bounding boxes for all target regions
    @return wimg: Perspective transformation image
    '''
    def detect(self, img):
        # Get the perspective transformation image
        wimg = self.getPerspectiveImage(img)
        # Get the HSV image
        hsv = cv.cvtColor(wimg, cv.COLOR_BGR2HSV)
        # Get the inverted grayscale image
        gray = 255 - cv.cvtColor(wimg, cv.COLOR_BGR2GRAY)
        # Perform Blob detection on the inverted grayscale image to obtain a list of key point information
        keypoints = self.detector.detect(gray)
        for kp in keypoints:
            # Get the center coordinates of key points
            x,y = np.array(kp.pt, dtype=np.int32)
            # Get the radius
            r = int(kp.size // 2)
            # Get the HSV image of key point regions
            rhsv = hsv[y-r:y+r, x-r:x+r]
            # Calculate the average hue of key point regions
            mrh = np.mean(rhsv[:, :, 0])
            # Calculate the average saturation of key point regions
            mrs = np.mean(rhsv[:, :, 1])
            # If the average hue of key point regions is greater than or equal to the minimum hue
            # Less than or equal to the maximum hue, and the average saturation is greater than the minimum saturation
            if mrh >= self.minH and mrh <= self.maxH and mrs > self.minS:
                # Add this key information
                self.addKeyinfo([x, y, r], kp)
        return self.bboxes, wimg

    '''
    Get the perspective transformation image
    @param img: Image
    @return rstimg: Perspective transformation image
    '''
    def getPerspectiveImage(self, img):
        # If the perspective transformation matrix is empty
        if self.transform is None:
            # Automatically obtain the image perspective transformation matrix
            self.transform = self.autoGetPerspectiveTransform(img)
        # Get the perspective transformation image
        rstimg = cv.warpPerspective(img, self.transform, tuple(self.size))
        # If the border extension size is not empty
        if self.borderSize is not None:
            # Get the border extension image
            rstimg = self.getBorderImage(rstimg, self.borderSize)
        return rstimg

    '''
    Get the border extension image
    @param img: Image
    @param size: Border extension size
    @return borderImg: Border extension image
    '''
    def getBorderImage(self, img, size):
        # Get the border extension image
        borderImg = cv.copyMakeBorder(img, size[1] // 2, size[1] // 2,size[0] // 2, size[0] // 2,
                                               cv.BORDER_CONSTANT, value=self.backColor)
        return borderImg

    '''
    Visualize Blob detection key points
    @param img: Image
    @return vimg: Visualization image
    '''
    def visualize(self, img):
        # Draw key point information on the image
        vimg = cv.drawKeypoints(img, self.keypoints, np.array([]), (0, 0, 255), cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        return vimg

    '''
    Add key information
    @param keyinfo: Key information (x, y, r)
    @param kp: Key point information
    '''
    def addKeyinfo(self, keyinfo, kp):
        # Unpack the key information
        x, y, r = keyinfo
        # Set the key information valid value to valid
        valid = True
        # Iterate through the key information list
        for info in self.keyinfos:
            # Unpack the current key information
            x2, y2, r2 = info
            # Calculate the distance between the key center coordinates and the current key center coordinates
            distance = getDistance([x, y], [x2, y2])
            # If the distance divided by the maximum radius is less than the minimum target distance radius multiple
            if distance / np.max([r, r2]) < self.minDistanceRadiusScale:
                # Set the key information valid value to invalid
                valid = False
                # Exit the loop
                break
        # If the length of the key information list is 0 or the key information is valid
        if len(self.keyinfos) == 0 or valid:
            # Add the key information to the key information list
            self.keyinfos.append(keyinfo)
            # Add the key point information to the key point information list
            self.keypoints.append(kp)
            # Add the key bbox to the key bbox list
            self.bboxes.append([x-r, y-r, 2*r, 2*r])

    '''
    Get the track binary image
    @param img: Image
    @param railBinary: Rail binary image
    '''
    def getRailBinary(self, img):
        # Get the grayscale image
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # Get the OTSU binary image, with the rail area as 0, the background area as 1, and other areas as 1
        _, binary = cv.threshold(gray, 0, 1, cv.THRESH_OTSU)
        # Get the binary image of the maximum area region, with both background and rail areas as 1, and other areas as 0
        maxBinary = getMaxAreaBinary(binary)
        # Get the average RGB value of the background area (used for boundary extension)
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
        # Initialize the rail binary image
        railBinary = np.zeros_like(railAreaBinary)
        # Fill the rail binary image with the rail contour list
        cv.drawContours(railBinary, contours, -1, 1, -1)
        return railBinary

    '''
    Automatically obtain the perspective transformation matrix
    @param img: Image
    @return transform: Perspective transformation matrix
    '''
    def autoGetPerspectiveTransform(self, img):
        # Get the rail binary image
        railBinary = self.getRailBinary(img)
        # Get the coordinates of the four corners of the rail area (top-left, top-right, bottom-right, bottom-left) as the source coordinate list
        srcPoints = getQuadrilateralPeakPoints(railBinary)
        # Get the target coordinate list based on the perspective transformation image size
        dstPoints = [[0, 0], [self.size[0], 0], [self.size[0], self.size[1]], [0, self.size[1]]]
        # Get the perspective transformation matrix
        transform = getPerspectiveTransform(srcPoints, dstPoints)
        return transform