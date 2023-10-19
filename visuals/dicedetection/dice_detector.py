import math

import cv2
import numpy as np

from utils.logger import LOG
from visuals import BoardVisuals
from visuals.BoardVisuals import BackgammonBoardVisuals


def detect_dice_sized_diff(img, min_radius_multiplier, max_radius_multiplier, param2=17):
    x1, y1 = BackgammonBoardVisuals.corners[0][0], BackgammonBoardVisuals.corners[0][1]
    x2, y2 = BackgammonBoardVisuals.corners[3][0], BackgammonBoardVisuals.corners[3][1]
    roi_img = img[y1:y2, x1:x2]

    # Load the image
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)

    # Preprocessing
    blurred = cv2.GaussianBlur(gray, (15, 15), 0)

    # Detect circles (potential dice)
    min_radius = int(BoardVisuals.BackgammonBoardVisuals.checker_diameter * min_radius_multiplier)
    max_radius = int(BoardVisuals.BackgammonBoardVisuals.checker_diameter * max_radius_multiplier)
    LOG.debug(f'Min radius: {min_radius}, Max radius: {max_radius}')

    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT,
                               dp=1.2,
                               minDist=min_radius * 2,
                               param1=50,
                               param2=param2,
                               minRadius=min_radius,
                               maxRadius=max_radius)

    # If circles are detected, add the offset to each circle's coordinates
    if circles is not None:
        img2 = img.copy()
        circles = np.round(circles[0, :]).astype("int")
        for circle in circles:
            circle[0] += x1  # add the x offset
            circle[1] += y1  # add the y offset
            cv2.circle(img2, (circle[0], circle[1]), circle[2], (0, 255, 0), 1)
        cv2.imshow('Circles', img2)
        cv2.waitKey(1)
    return img, circles


def detect_dice_value(img, circles):

    if circles is not None:
        dice_values = []

        for (x, y, r) in circles:
            r += 10  # expand the circle to ensure all blobs are properly visible
            # Draw the circle in the output image
            cv2.circle(img, (x, y), r, (0, 255, 0), 1)
            LOG.debug(f"Dice radius: {r}")

            # Extract the ROI
            roi = img[y - r:y + r, x - r:x + r]

            params = cv2.SimpleBlobDetector_Params()
            params.filterByArea = True
            params.minArea = 20  # Adjust as needed
            params.maxArea = 40
            params.filterByCircularity = True
            params.minCircularity = 0.8  # Adjust as needed

            # Create a blob detector with the parameters
            detector = cv2.SimpleBlobDetector_create(params)

            # Detect black blobs on the dice
            blobs_1 = detector.detect(roi)

            if blobs_1:
                LOG.debug(f'Blob size: {math.pi * (blobs_1[0].size / 2.0)**2}')
                # dice_values.append(len(blobs_1))
            # else:
                # Detect white blobs on the dice
            params.blobColor = 255
            detector = cv2.SimpleBlobDetector_create(params)
            blobs_2 = detector.detect(roi)

            keypoints = blobs_1 if len(blobs_1) > len(blobs_2) else blobs_2

            dice_values.append(len(keypoints))

            LOG.info(f'Dice value detected: {len(blobs_1)}')

            # Draw detected blobs on the image
            # Adjust keypoint positions and draw them on the original image
            for keypoint in keypoints:
                adjusted_x = int(keypoint.pt[0] + x - r)
                adjusted_y = int(keypoint.pt[1] + y - r)
                cv2.circle(img, (adjusted_x, adjusted_y), int(keypoint.size), (0, 0, 255), 2)

        dice_values.sort()
        return dice_values

    return []

'''
* Not detected -> 0
    * Have both moves
        * Get possible dice rolls, remove invalid moves, return a tuple of the possible combinations
    * Have only 1 move
        * If no more moves comes, the dice roll have to add up to the distance moved
        * If more moves come, the dice roll is the 2 distances covered
* Incorrectly detected
    * check is any of the moved distances match any of the detected dice values
    * the other one is the other distance covered
    * in case only one dice is moved to cover the value of both dice, get the possible dice values as the combination of the need to add up to the distance covered, we can then remove not possible rolls, for example the checker moved 6 positions, but there are opponents checkers on the 2nd and 3rd field
'''
