# board_detector.py
import cv2
import numpy as np


def detect_board_area(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_green = np.array([40, 30, 30])
    upper_green = np.array([90, 255, 180])

    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    green_mask = cv2.bitwise_not(green_mask)  # Invert the mask to get the area of interest

    _, thresh = cv2.threshold(green_mask, 60, 255, cv2.THRESH_BINARY_INV)
    thresh = cv2.GaussianBlur(thresh, (5, 5), 0)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    areas = [cv2.contourArea(cnt) for cnt in contours]
    sorted_contours = sorted(zip(areas, contours), key=lambda x: x[0], reverse=True)

    largest_rect = None
    second_largest_rect = None

    if len(sorted_contours) >= 2:
        # Draw and store the largest rectangle
        area, cnt = sorted_contours[0]
        x1, y1, w1, h1 = cv2.boundingRect(cnt)
        largest_rect = (x1, y1, w1, h1)
        cv2.rectangle(image, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 2)

        # Draw and store the second-largest rectangle
        _, cnt2 = sorted_contours[1]
        x2, y2, _, h2 = cv2.boundingRect(cnt2)
        second_largest_rect = (x1, y2, w1, h2)
        cv2.rectangle(image, (x1, y2), (x1 + w1, y2 + h2), (0, 255, 0), 2)

    return largest_rect, second_largest_rect


def get_roi(image, largest_rect, second_largest_rect):
    if largest_rect is None or second_largest_rect is None:
        return None

    x1, y1, w1, h1 = largest_rect
    x2, y2, w2, h2 = second_largest_rect

    top_left_x = min(x1, x2)
    top_left_y = min(y1, y2)
    bottom_right_x = max(x1 + w1, x2 + w2)
    bottom_right_y = max(y1 + h1, y2 + h2)

    roi = image[top_left_y:bottom_right_y, top_left_x:bottom_right_x]
    return roi
