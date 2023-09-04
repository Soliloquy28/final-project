import cv2 as cv
import numpy as np

'''
获取两点距离
@param p1：点1
@param p2：点2
@return distance：两点距离
'''
def getDistance(p1, p2):
    p1 = np.array(p1)
    p2 = np.array(p2)
    distance = np.linalg.norm(p1-p2)
    return distance

'''
获取外轮廓列表
@param binary：二值图
@return contours：外轮廓列表
'''
def getContours(binary):
    contours, hierarchy = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    contours = np.array(contours, dtype=object)
    return contours

'''
获取最大面积二值图
@param binary：二值图
@return maxBinary：最大面积二值图
'''
def getMaxAreaBinary(binary):
    maxBinary = np.zeros_like(binary)
    contours = getContours(binary)
    areas = [cv.contourArea(cnt) for cnt in contours]
    cv.drawContours(maxBinary, contours, np.argmax(areas), 1, -1)
    return maxBinary

'''
获取二值图前景区域四个顶点坐标（左上，右上，右下，左下）
@param binary：二值图
@return peakPoints：二值图前景区域四个顶点坐标（左上，右上，右下，左下）
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
获取透视变换矩阵
@param srcPoints：起始坐标列表
@param dstPoints：目标坐标列表
@return transform：透视变换矩阵
'''
def getPerspectiveTransform(srcPoints, dstPoints):
    srcPoints = np.float32(srcPoints)
    dstPoints = np.float32(dstPoints)
    transform = cv.getPerspectiveTransform(srcPoints, dstPoints)
    return transform

# 轨道目标检测器
class RailDetector:
    
    '''
    构造函数
    @param minH：最小色相
    @param maxH：最大色相
    @param minS：最小饱和度
    @param size：透视变换图尺寸
    @param borderSize：边界拓展尺寸
    @param minDistanceRadiusScale：最小目标距离半径倍数，目标间相切为2
    '''
    def __init__(self, minH, maxH, minS, size, borderSize=None, minDistanceRadiusScale=2):
        # 初始化关键信息列表
        self.keyinfos = []
        # 初始化关键点信息列表
        self.keypoints = []
        # 初始化关键bbox列表
        self.bboxes = []
        # 初始化透视变换矩阵为空
        self.transform = None
        # 初始化背景颜色为空
        self.backColor = None
        # 初始化最小色相
        self.minH = minH
        # 初始化最大色相
        self.maxH = maxH
        # 初始化最小饱和度
        self.minS = minS
        # 初始化透视变换图尺寸
        self.size = size
        # 初始化边界拓展尺寸
        self.borderSize = borderSize
        # 初始化最小目标距离半径倍数
        self.minDistanceRadiusScale = minDistanceRadiusScale
        # 获取Blob检测器参数列表
        self.params = cv.SimpleBlobDetector_Params()
        # 获取Blob检测器
        self.detector = cv.SimpleBlobDetector_create(self.params)
    
    '''
    坚持检测，直到检测数量为目标数量为止
    @param videoPath：视频路径
    @param count：目标数量
    @return self.bboxes：关键bbox列表
    @return wimg：透视变换图
    '''
    def keepDetect(self, videoPath, count):
        # 加载视频读取器
        _cap = cv.VideoCapture(videoPath)
        # 初始化透视变换图
        wimg = None
        # 循环检测每一帧，直到检测数量为目标数量为止
        while True:
            # 读取下一帧
            success, frame = _cap.read()
            # 如果读取成功
            if success == False:
                break
            try:
                # 目标检测，并返回透视变换图
                _, wimg = self.detect(frame)
            except:
                pass
            # 如果关键信息列表长度和目标数量相等，退出检测
            if len(self.keyinfos) == count:
                break
        # 释放视频读取器
        _cap.release()
        return self.bboxes, wimg
    
    '''
    目标检测
    @param img：图像
    @return self.bboxes：所有目标区域bbox列表
    @return wimg：获取透视变换图
    '''
    def detect(self, img):
        # 获取透视变换图
        wimg = self.getPerspectiveImage(img)
        # 获取HSV图
        hsv = cv.cvtColor(wimg, cv.COLOR_BGR2HSV)
        # 获取反相灰度图
        gray = 255 - cv.cvtColor(wimg, cv.COLOR_BGR2GRAY)
        # Blob检测反相灰度图，得到关键点信息列表
        keypoints = self.detector.detect(gray)
        for kp in keypoints:
            # 获取关键点的中心坐标
            x,y = np.array(kp.pt, dtype=np.int32)
            # 获取半径
            r = int(kp.size // 2)
            # 获取关键点区域的HSV图
            rhsv = hsv[y-r:y+r, x-r:x+r]
            # 计算关键点区域的平均色相
            mrh = np.mean(rhsv[:, :, 0])
            # 计算关键点区域的平均饱和度
            mrs = np.mean(rhsv[:, :, 1])
            # 如果关键点区域的平均色相大于等于最小色相
            # 小于等于最大色相，且平均饱和度大于最小饱和度
            if mrh >= self.minH and mrh <= self.maxH and mrs > self.minS:
                # 添加该关键信息
                self.addKeyinfo([x, y, r], kp)
                print(type(kp))
        return self.bboxes, wimg
    
    '''
    获取透视变换图
    @param img：图像
    @return rstimg：获取透视变换图
    '''
    def getPerspectiveImage(self, img):
        # 如果透视变换矩阵为空
        if self.transform is None:
            # 自动获取图像透视变换矩阵
            self.transform = self.autoGetPerspectiveTransform(img)
        # 获取透视变换图
        rstimg = cv.warpPerspective(img, self.transform, tuple(self.size))
        # 如果边界拓展尺寸不为空
        if self.borderSize is not None:
            # 获取边界拓展图
            rstimg = self.getBorderImage(rstimg, self.borderSize)
        return rstimg
    
    '''
    获取边界拓展图
    @param img：图像
    @param size：边界拓展尺寸
    @return borderImg：边界拓展图
    '''
    def getBorderImage(self, img, size):
        # 获取边界拓展图
        borderImg = cv.copyMakeBorder(img, size[1] // 2, size[1] // 2,size[0] // 2, size[0] // 2,
                                               cv.BORDER_CONSTANT, value=self.backColor)
        return borderImg
    
    '''
    可视化Blob检测关键点
    @param img：图像
    @return vimg：可视化图
    '''
    def visualize(self, img):
        # 绘制关键点信息到图像中
        vimg = cv.drawKeypoints(img, self.keypoints, np.array([]), (0, 0, 255), cv.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        return vimg
    
    '''
    添加关键信息
    @param keyinfo：关键信息（x,y,r）
    @param kp：关键点信息
    '''
    def addKeyinfo(self, keyinfo, kp):
        # 解开关键信息
        x, y, r = keyinfo
        # 设置关键信息有效值为有效
        valid = True
        # 遍历关键信息列表
        for info in self.keyinfos:
            # 解开当前关键信息
            x2, y2, r2 = info
            # 获取关键中心坐标与当前关键中心坐标的距离
            distance = getDistance([x, y], [x2, y2])
            # 如果距离除最大半径小于最小目标距离半径倍数
            if distance / np.max([r, r2]) < self.minDistanceRadiusScale:
                # 设置关键信息有效值为无效
                valid = False
                # 退出循环
                break
        # 如果关键信息列表长度为0或者关键信息有效
        if len(self.keyinfos) == 0 or valid:
            # 将关键信息添加到关键信息列表
            self.keyinfos.append(keyinfo)
            # 将关键点信息添加到关键点信息列表
            self.keypoints.append(kp)
            # 将关键bbox添加到关键bbox列表
            self.bboxes.append([x-r, y-r, 2*r, 2*r])
    
    '''
    获取轨道二值图
    @param img：图像
    @param railBinary：轨道二值图
    '''
    def getRailBinary(self, img):
        # 获取灰度图
        gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # 获取OTSU二值图，轨道区域为0，背景区域为1，其他区域为1
        _, binary = cv.threshold(gray, 0, 1, cv.THRESH_OTSU)
        # 获取最大面积区域二值图，背景和轨道区域均为1，其他区域为0
        maxBinary = getMaxAreaBinary(binary)
        # 获取背景区域的平均RGB值（用于边界拓展）
        self.backColor = np.round(np.mean(img[(maxBinary > 0) & (binary > 0)], axis=0)).astype(np.uint8).tolist()
        # 获取轨道区域二值图
        railAreaBinary = np.uint8((maxBinary > 0) & (binary == 0))
        # 获取轨道区域二值图外轮廓列表
        contours = getContours(railAreaBinary)
        # 获取外轮廓周长列表
        lengths = np.array([cv.arcLength(cnt, True) for cnt in contours])
        # 获取周长大于最大周长一半的外轮廓列表，即是轨道外轮廓列表，主要为了过滤非轨道外轮廓
        contours = contours[lengths > np.max(lengths) // 2]
        # 初始化轨道二值图
        railBinary = np.zeros_like(railAreaBinary)
        # 将轨道外轮廓列表填充到轨道二值图
        cv.drawContours(railBinary, contours, -1, 1, -1)
        return railBinary
    
    '''
    自动获取透视变换矩阵
    @param img：图像
    @return transform：透视变换矩阵
    '''
    def autoGetPerspectiveTransform(self, img):
        # 获取轨道二值图
        railBinary = self.getRailBinary(img)
        # 获取轨道四个顶点坐标（左上，右上，右下，左下）为起始坐标列表
        srcPoints = getQuadrilateralPeakPoints(railBinary)
        # 根据透视变换图尺寸获取目标坐标列表
        dstPoints = [[0, 0], [self.size[0], 0], [self.size[0], self.size[1]], [0, self.size[1]]]
        # 获取透视变换矩阵
        transform = getPerspectiveTransform(srcPoints, dstPoints)
        return transform