import logging

import cv2
import numpy as np

from utils.logger import LOG
from visuals import BoardVisuals
from visuals.BoardVisuals import BackgammonBoardVisuals


def detect_dice(img):
    x1, y1 = BackgammonBoardVisuals.corners[0][0], BackgammonBoardVisuals.corners[0][1]
    x2, y2 = BackgammonBoardVisuals.corners[3][0], BackgammonBoardVisuals.corners[3][1]
    img = img[y1:y2, x1:x2]

    # Load the image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Preprocessing
    blurred = cv2.GaussianBlur(gray, (15, 15), 0)

    # Detect circles (potential dice)
    min_radius = int(BoardVisuals.BackgammonBoardVisuals.checker_diameter * 0.125)
    max_radius = int(BoardVisuals.BackgammonBoardVisuals.checker_diameter * 0.3)

    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT,
                               dp=1.2,
                               minDist=30,
                               param1=50,
                               param2=20,
                               minRadius=min_radius,
                               maxRadius=max_radius)

    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")
        dice_values = []

        for (x, y, r) in circles:
            # Draw the circle in the output image
            cv2.circle(img, (x, y), r, (0, 255, 0), 2)
            LOG.info(f"Dice radius: {r}")

            # Extract the ROI
            roi = gray[y - r:y + r, x - r:x + r]

            # Threshold the ROI
            _, thresh = cv2.threshold(roi, 127, 255, cv2.THRESH_BINARY_INV)

            # Find contours in the thresholded ROI
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Count the number of contours (dots on the dice)
            dice_values.append(len(contours))
            LOG.info(f"Dice value detected: {len(contours)}")

        cv2.imshow('Detected dice', img)

        return dice_values

    return []
