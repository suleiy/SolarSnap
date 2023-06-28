from __future__ import print_function
from PIL import Image
import cv2
import os
import matplotlib.pyplot as plt
import numpy as np
import math 
import glob
from shapely.geometry import Polygon
from PIL import Image, ImageEnhance

zoom = 20
tileSize = 256
initialResolution = 2 * math.pi * 6378137 / tileSize
originShift = 2 * math.pi * 6378137 / 2.0
earthc = 6378137 * 2 * math.pi
factor = math.pow(2, zoom)
map_width = 256 * (2 ** zoom)
red=(255,0,0)
blue=(0,0,255)


def grays(im):
    return cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
def white_image(im):
    return cv2.bitwise_not(np.zeros(im.shape, np.uint8))
def pixels_per_mm(lat, length):
    return length / math.cos(lat * math.pi / 180) * earthc * 1000 / map_width
def sharp(gray):
    blur = cv2.bilateralFilter(gray, 5, sigmaColor=7, sigmaSpace=5)
    kernel_sharp = np.array((
        [-2, -2, -2],
        [-2, 17, -2],
        [-2, -2, -2]), dtype='int')
    return cv2.filter2D(blur, -1, kernel_sharp)



def contours_canny(cnts, canny_contours, edged, canny_polygons):
    cv2.drawContours(canny_contours, cnts, -1, 255, 1)

    # Removing the contours detected inside the roof
    for cnt in cnts:
        counters = 0
        cnt = np.array(cnt)
        cnt = np.reshape(cnt, (cnt.shape[0], cnt.shape[2]))
        pts = []

        if cv2.contourArea(cnt) > 10:
            for i in cnt:
                x, y = i
                if edged[y, x] == 255:
                    counters += 1
                    pts.append((x, y))

        if counters > 10:
            pts = np.array(pts)
            pts = pts.reshape(-1, 1, 2)
            cv2.polylines(canny_polygons, [pts], True, 0)


def contours_img(cnts,image_contours,edged,image_polygons):
    cv2.drawContours(image_contours, cnts, -1, 255, 1)

    # Removing the contours detected inside the roof
    for cnt in cnts:
        counter = 0
        cnt = np.array(cnt)
        cnt = np.reshape(cnt, (cnt.shape[0], cnt.shape[2]))
        pts = []
        if cv2.contourArea(cnt) > 5:
            for i in cnt:
                x, y = i
                if edged[y, x] == 255:
                    counter += 1
                    pts.append((x, y))
        if counter > 10:
            pts = np.array(pts)
            pts = pts.reshape(-1, 1, 2)
            cv2.polylines(image_polygons, [pts], True, 0)


def rotation(center_x, center_y, points, ang):
    angle = ang * math.pi / 180
    rotated_points = []
    for p in points:
        x, y = p
        x, y = x - center_x, y - center_y
        x, y = (x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle))
        x, y = x + center_x, y + center_y
        rotated_points.append((x, y))
    return rotated_points


def createLineIterator(P1, P2, img):
    imageH = img.shape[0]
    imageW = img.shape[1]
    P1X = P1[0]
    P1Y = P1[1]
    P2X = P2[0]
    P2Y = P2[1]

    # difference and absolute difference between points
    # used to calculate slope and relative location between points
    dX = P2X - P1X
    dY = P2Y - P1Y
    dXa = np.abs(dX)
    dYa = np.abs(dY)

    # predefine numpy array for output based on distance between points
    itbuffer = np.empty(shape=(np.maximum(dYa, dXa), 3), dtype=np.float32)
    itbuffer.fill(np.nan)

    # Obtain coordinates along the line using a form of Bresenham's algorithm
    negY = P1Y > P2Y
    negX = P1X > P2X
    if P1X == P2X:  # vertical line segment
        itbuffer[:, 0] = P1X
        if negY:
            itbuffer[:, 1] = np.arange(P1Y - 1, P1Y - dYa - 1, -1)
        else:
            itbuffer[:, 1] = np.arange(P1Y + 1, P1Y + dYa + 1)
    elif P1Y == P2Y:  # horizontal line segment
        itbuffer[:, 1] = P1Y
        if negX:
            itbuffer[:, 0] = np.arange(P1X - 1, P1X - dXa - 1, -1)
        else:
            itbuffer[:, 0] = np.arange(P1X + 1, P1X + dXa + 1)
    else:  # diagonal line segment
        steepSlope = dYa > dXa
        if steepSlope:
            slope = dX.astype(float) / dY.astype(float)
            if negY:
                itbuffer[:, 1] = np.arange(P1Y - 1, P1Y - dYa - 1, -1)
            else:
                itbuffer[:, 1] = np.arange(P1Y + 1, P1Y + dYa + 1)
            itbuffer[:, 0] = (slope * (itbuffer[:, 1] - P1Y)).astype(int) + P1X
        else:
            slope = dY.astype(float) / dX.astype(float)
            if negX:
                itbuffer[:, 0] = np.arange(P1X - 1, P1X - dXa - 1, -1)
            else:
                itbuffer[:, 0] = np.arange(P1X + 1, P1X + dXa + 1)
            itbuffer[:, 1] = (slope * (itbuffer[:, 0] - P1X)).astype(int) + P1Y

    # Remove points outside of image
    colX = itbuffer[:, 0]
    colY = itbuffer[:, 1]
    itbuffer = itbuffer[(colX >= 0) & (colY >= 0) & (colX < imageW) & (colY < imageH)]

    # Get intensities from img ndarray
    itbuffer[:, 2] = img[itbuffer[:, 1].astype(np.uint), itbuffer[:, 0].astype(np.uint)]

    return itbuffer

def panel_rotation(panels_series, solar_roof_area,color,new_image,high_reso_orig, l, w,pw,pl,solar_angle):
    high_reso = cv2.pyrUp(solar_roof_area)
    rows, cols = high_reso.shape
    high_reso_new = cv2.pyrUp(new_image)
    squares = []
    high_reso_orig_withShape=high_reso_orig.copy()

    for _ in range(panels_series - 2):
        for col in range(0, cols, l + 1):
            for row in range(0, rows, w + 1):

                # Rectangular Region of interest for solar panel area
                solar_patch = high_reso[row:row + (w + 1) * pw + 1, col:col + ((l * pl) + 3)]
                r, c = solar_patch.shape
                #c is length, r is width 

                # Rotation of rectangular patch according to the angle provided
                patch_rotate = np.array([[col, row], [c + col, row], [c + col, r + row], [col, r + row]], np.int32)
                rotated_patch_points = rotation((col + c) / 2, row + r / 2, patch_rotate, solar_angle)
                rotated_patch_points = np.array(rotated_patch_points, np.int32)

                # Check for if rotated points go outside of the image
                if (rotated_patch_points > 0).all():
                    solar_polygon = Polygon(rotated_patch_points)
                    polygon_points = np.array(solar_polygon.exterior.coords, np.int32)

                    # Appending points of the image inside the solar area to check the intensity
                    patch_intensity_check = []

                    # Point polygon test for each rotated solar patch area
                    for j in range(rows):
                        for k in range(cols):
                            if cv2.pointPolygonTest(polygon_points, (k, j), False) == 1:
                                patch_intensity_check.append(high_reso[j, k])

                    # Check for the region available for Solar Panels
                    if np.mean(patch_intensity_check) == 255:

                        # Moving along the length of line to segment solar panels in the patch
                        solar_line_1 = createLineIterator(rotated_patch_points[0], rotated_patch_points[1], high_reso)
                        solar_line_1 = solar_line_1.astype(int)
                        solar_line_2 = createLineIterator(rotated_patch_points[3], rotated_patch_points[2], high_reso)
                        solar_line_2 = solar_line_2.astype(int)
                        line1_points = []
                        line2_points = []
                        if len(solar_line_2) > 10 and len(solar_line_1) > 10:

                            # Remove small unwanted patches
                            cv2.fillPoly(high_reso, [rotated_patch_points], 0)
                            cv2.fillPoly(high_reso_new, [rotated_patch_points], 0)
                            cv2.polylines(high_reso_orig, [rotated_patch_points], 1, 0, 2)
                            cv2.polylines(high_reso_new, [rotated_patch_points], 1, 0, 2)

                            cv2.fillPoly(high_reso_orig, [rotated_patch_points], (0, 0, 255)) #roof w panels
                            cv2.fillPoly(high_reso_new, [rotated_patch_points], (0, 0, 255))#panels

                            for i in range(5, len(solar_line_1), 5):
                                line1_points.append(solar_line_1[i])
                            for i in range(5, len(solar_line_2), 5):
                                line2_points.append(solar_line_2[i])

                            panels1=[]
                            panels2=[]
                            # print(line1_points)
                            # print(line2_points)
                            for i in range(0, len(solar_line_1), 5):
                                panels1.append(solar_line_1[i])
                            for i in range(0, len(solar_line_2), 5):
                                panels2.append(solar_line_2[i])

                            min_length = min(len(panels1), len(panels2))

                            # Iterate through the zipped arrays
                            for i in range(min_length - 1):
                                square = np.array([panels1[i][:2], panels2[i][:2], panels2[i+1][:2], panels1[i+1][:2]])
                                squares.append(square)

                            # Segmenting Solar Panels in the Solar Patch
                            for points1, points2 in zip(line1_points, line2_points):
                                x1, y1, _ = points1
                                x2, y2, _ = points2
                                cv2.line(high_reso_orig, (x1, y1), (x2, y2), (0, 0, 0), 1)
                                cv2.line(high_reso_new, (x1, y1), (x2, y2), (0, 0, 0), 1)

        # Number of Solar Panels in series (3/4/5)
        panels_series = panels_series - 1
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
    
    if color=="black":
        panelImg=os.path.join(ROOT_DIR,"static","black.png")
    if color=="brown":
        panelImg=os.path.join(ROOT_DIR,"static","blue.png")
    if color=="blue":
        panelImg=os.path.join(ROOT_DIR,"static","brown.png")
    if color=="silver":
        panelImg=os.path.join(ROOT_DIR,"static","silver.png")
    # print(squares)
    for square in squares:
        panel = cv2.imread(panelImg)
        rect = cv2.minAreaRect(np.array(square))
        box = cv2.boxPoints(rect)
        hull = cv2.convexHull(box)
        box = np.int0(box)
        width = int(rect[1][0])
        height = int(rect[1][1])
        matrix = cv2.getPerspectiveTransform(np.float32([[0, 0], [width, 0], [width, height], [0, height]]),
                                            np.float32(box))
        insert_image_warped = cv2.warpPerspective(panel, matrix, (high_reso_orig_withShape.shape[1], high_reso_orig_withShape.shape[0]))

        # Create a mask with the same size as the high-resolution original image
        mask = np.zeros_like(high_reso_orig_withShape)

        # Fill the mask with white in the region of the box
        cv2.fillPoly(mask, [box], (255, 255, 255))

        # Replace the corresponding region in the original image with the warped panel image
        high_reso_orig_withShape = high_reso_orig_withShape & cv2.bitwise_not(mask)
        high_reso_orig_withShape = high_reso_orig_withShape + cv2.bitwise_and(insert_image_warped, mask)

    result_3=Image.fromarray(high_reso_orig_withShape)
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path=os.path.join(BASE_DIR,"static/src/vue/dist","output.jpg")
    result_3.save(path, 'JPEG')
    # plt.title("with pictures")
    # plt.imshow(high_reso_orig_withShape)
    # plt.show()
def getColor(color):
    return color
if __name__ == "__main__":
    color=getColor(color)
    pl, pw, l, w, solar_angle = 4, 1, 8, 5, 30
    image = cv2.imread('input.jpg') #input image path 
    img = cv2.pyrDown(image)
    print('image shape : ',img.shape)
    n_white_pix = np.sum(img==255)
    # Upscaling of Image
    high_reso_orig = cv2.pyrUp(image)
    high_reso_orig_withShape=high_reso_orig

    # White blank image for contours of Canny Edge Image
    canny_contours = white_image(image)
    # White blank image for contours of original image
    image_contours = white_image(image)

    # White blank images removing rooftop's obstruction
    image_polygons = grays(canny_contours)
    canny_polygons = grays(canny_contours)

    # Gray Image
    grayscale = grays(image)
    plt.figure()
    plt.title('grayscale')
    plt.imshow(image, cmap='gray')
    # Edge Sharpened Image
    sharp_image = sharp(grayscale)
    # Canny Edge
    edged = cv2.Canny(sharp_image, 180, 240)
    edge_image = sharp_image      
    # Otsu Threshold (Adaptive Threshold)
    # thresh = cv2.threshold(sharp_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    thresh = cv2.threshold(sharp_image, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    # Contours in Original Image
    contours_img(cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2], image_contours,edged,image_polygons)
    # Contours in Canny Edge Image
    contours_canny(cv2.findContours(edged, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[-2], canny_contours, edged, canny_polygons)
    # Optimum place for placing Solar Panels
    solar_roof = cv2.bitwise_and(image_polygons, canny_polygons)
    #print('solar white pix : ',n_white_pix)
    print('size of solar roof : ',solar_roof.shape)
    new_image = white_image(image)
    ret, thresh2 = cv2.threshold(edge_image, 198, 255, cv2.THRESH_BINARY)
    n_white_pix = np.sum(thresh2==255)
    area_roof = n_white_pix*0.075
    print('area of building roof : ',n_white_pix*0.075,'sqm')
    print('new image shape',new_image.shape)
    
    # Rotation of Solar Panels
    panel_rotation(pl, solar_roof, color)