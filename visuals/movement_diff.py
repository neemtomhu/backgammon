import math

import cv2
import numpy as np

from utils.logger import LOG
from visuals import BoardVisuals
from visuals.BoardVisuals import BackgammonBoardVisuals
from visuals.checker_detector import get_checker_movement
from visuals.dicedetection.dice_detector import detect_dice_sized_diff, detect_dice_value


def get_anchor_frame(cap, start_pos=1, time_limit_secs=10):
    LOG.info('Detecting anchor frame')
    LOG.info(cv2.__version__)

    # Set the starting position
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_pos)

    # Read the first frame and convert to grayscale
    ret, prev_img = cap.read()
    if not ret:
        return None  # Return None if unable to read the frame
    prev_img = cv2.cvtColor(prev_img, cv2.COLOR_BGR2GRAY)
    prev_img = cv2.resize(prev_img, (640, 480))  # Resize to a smaller resolution

    # Initialize variables
    min_diff = float('inf')
    anchor_frame_pos = start_pos
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frame_count = 0

    while True:
        # Jump 10 frames ahead
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_pos + frame_count * 10)
        ret, current_img = cap.read()

        if not ret:
            break

        current_img = cv2.cvtColor(current_img, cv2.COLOR_BGR2GRAY)
        current_img = cv2.resize(current_img, (640, 480))

        # Compute the difference
        difference = cv2.absdiff(prev_img, current_img)
        total_diff = np.sum(difference)

        # Update the anchor frame if the current difference is the smallest
        if total_diff < min_diff:
            min_diff = total_diff
            anchor_frame_pos = start_pos + frame_count * 10

        # Early stopping
        if total_diff < 1000:  # Arbitrary threshold, adjust as needed
            break

        # Update the previous image and frame count
        prev_img = current_img
        frame_count += 1

        # Check time limit
        if frame_count * 10 / fps > time_limit_secs:
            break

    LOG.info(f'Detected anchor frame position: {anchor_frame_pos}')
    return anchor_frame_pos


def get_next_move_frame(cap, anchor_frame_pos, calm_duration_secs=2):
    LOG.info('Detecting movement frame after anchor frame')
    lower_threshold = ((BoardVisuals.BackgammonBoardVisuals.checker_diameter / 2) ** 2 * math.pi) * 1
    upper_threshold = ((BoardVisuals.BackgammonBoardVisuals.checker_diameter / 2) ** 2 * math.pi) * 3

    cap.set(cv2.CAP_PROP_POS_FRAMES, anchor_frame_pos)
    ret, anchor_img = cap.read()
    if not ret:
        return None
    anchor_img = cv2.cvtColor(anchor_img, cv2.COLOR_BGR2GRAY)

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    frames_to_check = int(fps * calm_duration_secs)
    frame_count = 0

    stable_frame_pos = None
    while True:
        ret, current_img = cap.read()
        if not ret:
            break

        current_img = cv2.cvtColor(current_img, cv2.COLOR_BGR2GRAY)

        difference = cv2.absdiff(anchor_img, current_img)
        _, binary_diff = cv2.threshold(difference, 25, 255, cv2.THRESH_BINARY)  # Adjust threshold as needed

        contours, _ = cv2.findContours(binary_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_area = sum(cv2.contourArea(contour) for contour in contours if
                         lower_threshold <= cv2.contourArea(contour) <= upper_threshold)

        if valid_area > 0:

            is_calm = True
            for _ in range(frames_to_check):
                ret, next_img = cap.read()
                frame_count += 1
                if not ret:
                    is_calm = False
                    break
                next_img = cv2.cvtColor(next_img, cv2.COLOR_BGR2GRAY)
                next_diff = cv2.absdiff(current_img, next_img)
                _, binary_next_diff = cv2.threshold(next_diff, 25, 255, cv2.THRESH_BINARY)  # Adjust threshold as needed

                next_contours, _ = cv2.findContours(binary_next_diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                next_valid_area = sum(cv2.contourArea(contour) for contour in next_contours if
                                      lower_threshold <= cv2.contourArea(contour) <= upper_threshold)

                LOG.debug(f'next_valid_area={next_valid_area}')
                if next_valid_area > upper_threshold:
                    is_calm = False
                    break

            if is_calm:
                stable_frame_pos = anchor_frame_pos + frame_count
                cv2.drawContours(current_img, next_contours, -1, (0, 255, 0), 2)
                # cv2.imshow('Detected Differences', current_img)
                break

        frame_count += 1
        LOG.debug(
            f'Frame count: {frame_count}\n lower_threshold={lower_threshold}, upper_threshold={upper_threshold}, valid_area={valid_area}')

    LOG.info(f'Detected movement frame position: {stable_frame_pos}')
    return stable_frame_pos


def highlight_diff(image1, image2):
    difference = cv2.absdiff(image1, image2)
    LOG.info(f'Difference in px: {np.sum(difference > 0)}')

    # Convert the difference to grayscale
    gray_difference = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    # Threshold the difference
    _, thresh = cv2.threshold(gray_difference, 20, 255, cv2.THRESH_BINARY)

    # Morphological Opening
    kernel = np.ones((5, 5), np.uint8)
    opened = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

    # Optional: Find contours to highlight the differences
    contours, _ = cv2.findContours(opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    min_area = BoardVisuals.BackgammonBoardVisuals.checker_diameter ** 2 * 3.14 * 0.1
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(image1, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.rectangle(image2, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Display the images
    # cv2.imshow('Image 1', image1)
    # cv2.imshow('Image 2', image2)
    # cv2.imshow('Difference', difference)
    # cv2.imshow('Thresholded Difference', thresh)

    return difference


def extract_difference(img1, img2, threshold=20):
    x1, y1 = BackgammonBoardVisuals.corners[0][0], BackgammonBoardVisuals.corners[0][1]
    x2, y2 = BackgammonBoardVisuals.corners[3][0], BackgammonBoardVisuals.corners[3][1]
    roi_img1 = img1[y1:y2, x1:x2]
    roi_img2 = img2[y1:y2, x1:x2]


    if roi_img1 is None or roi_img2 is None:
        print("Error loading images.")
        return None

    # Calculate the absolute difference between the two images
    difference = cv2.absdiff(roi_img1, roi_img2)

    # Convert the difference to grayscale
    gray_difference = cv2.cvtColor(difference, cv2.COLOR_BGR2GRAY)

    # Threshold the difference
    _, thresh = cv2.threshold(gray_difference, threshold, 255, cv2.THRESH_BINARY)
    # cv2.imshow('Threshold diff', thresh)

    # Find contours in the thresholded difference
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Create an all black image
    black_background = np.zeros_like(img2)

    # Define a minimum and a maximum area threshold
    min_area_threshold = (BoardVisuals.BackgammonBoardVisuals.checker_diameter / 2)**2 * math.pi * 0.1
    max_area_threshold = (BoardVisuals.BackgammonBoardVisuals.checker_diameter / 2)**2 * math.pi * 4

    # Loop over the contours
    for contour in contours:
        # Calculate the area of the contour
        area = cv2.contourArea(contour)
        # Only process contours that are above the area threshold
        if max_area_threshold > area > min_area_threshold:
            # Get the bounding box of the contour
            x, y, w, h = cv2.boundingRect(contour)

            # Cut out the difference from the second image and put it on the black background
            black_background[y + y1:y + y1 + h, x + x1:x + x1 + w] = img2[y + y1:y + y1 + h, x + x1:x + x1 + w]

    # Show the result
    # cv2.imshow('Result', black_background)
    # cv2.waitKey(1)
    return black_background


def detect_movement_type(img):
    # Look for checker sized changes
    detected_img, circles = detect_dice_sized_diff(
        img,
        min_radius_multiplier=0.45,
        max_radius_multiplier=0.65,
        param2=25)

    if circles is not None:
        LOG.info('Checker movement detected')
        get_checker_movement(detected_img, circles)
        # return "Checker movement"

    # Look fod dice sized changes
    detected_img, circles = detect_dice_sized_diff(
        img,
        min_radius_multiplier=0.2,
        max_radius_multiplier=0.4,
        param2=17)
    if circles is not None:
        LOG.info('Dice roll detected')
        detect_dice_value(detected_img, circles)
        # return "Dice roll"
