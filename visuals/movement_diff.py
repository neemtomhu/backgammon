import math

import cv2
import numpy as np

from utils.logger import LOG
from visuals import BoardVisuals
from visuals.BoardVisuals import BackgammonBoardVisuals
# from visuals.checker_detector import get_checker_movement


def get_anchor_frame(cap, start_pos=1, time_limit_secs=10):
    LOG.info('Detecting anchor frame')
    LOG.info(f'OpenCV version: {cv2.__version__}')

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


def get_next_move_frame(cap, anchor_frame_pos, board_roi, area_thresh=1000, frames_to_skip=19):
    # Set the video position to the anchor frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, anchor_frame_pos)
    LOG.debug('Detecting next move frame')
    ret, anchor_frame = cap.read()
    if not ret:
        return None

    # Convert anchor frame to grayscale
    anchor_gray = cv2.cvtColor(anchor_frame, cv2.COLOR_BGR2GRAY)

    # Create a mask for the region outside the board
    mask = np.ones_like(anchor_gray) * 255

    # Convert board_roi to a list of lists for modification
    board_roi_list = [list(point) for point in board_roi]

    # Calculate the height of the ROI
    height = abs(board_roi[2][1] - board_roi[0][1])
    padding = int(0.1 * height)

    # Add padding to the top-most point
    board_roi_list[0][1] -= padding
    board_roi_list[1][1] -= padding

    # Add padding to the bottom-most point
    board_roi_list[2][1] += padding
    board_roi_list[3][1] += padding

    # Convert back to a list of tuples
    board_roi = [tuple(point) for point in board_roi_list]

    # Rearrange the board_roi points
    board_roi = [board_roi[0], board_roi[1], board_roi[3], board_roi[2]]
    pts = np.array(board_roi, np.int32)
    pts = pts.reshape((-1, 1, 2))
    cv2.fillPoly(mask, [pts], 0)

    # Apply the mask to the anchor frame
    anchor_gray_masked = cv2.bitwise_and(anchor_gray, mask)

    hand_in_frame = False

    while True:
        cv2.waitKey(1)
        # Increment frame position
        current_pos = cap.get(cv2.CAP_PROP_POS_FRAMES)
        LOG.debug(f'Processing position: {current_pos}')
        next_pos = current_pos + frames_to_skip
        if next_pos > cap.get(cv2.CAP_PROP_FRAME_COUNT):
            return current_pos

        cap.set(cv2.CAP_PROP_POS_FRAMES, current_pos + frames_to_skip)

        ret, frame = cap.read()
        if not ret:
            break

        # Convert current frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply the mask to the current frame
        gray_masked = cv2.bitwise_and(gray, mask)

        # Calculate absolute difference between current frame and anchor frame
        diff = cv2.absdiff(gray_masked, anchor_gray_masked)

        # Threshold the difference image
        _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Check if any contour is large enough to be the hand
        areas = []
        for contour in contours:
            area = cv2.contourArea(contour)
            areas.append(area)
            cv2.drawContours(frame, [contour], -1, (0, 255, 0), 2)
            if area > area_thresh:
                LOG.debug(f'Hand movement area: {area}')
                # cv2.imshow('Hand in frame', frame)
                hand_in_frame = True
                # break

        if areas:
            LOG.info(f'Max area: {max(areas)}')

        if hand_in_frame and not any(cv2.contourArea(contour) > area_thresh for contour in contours):
            # Hand was in the frame in the previous iteration but not now
            # cv2.imshow('Next move', frame)
            # cv2.waitKey(1)
            if areas:
                LOG.info(f'Max contour area: {max(areas)}')
            return int(cap.get(cv2.CAP_PROP_POS_FRAMES))

    return None


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
    max_area_threshold = (BoardVisuals.BackgammonBoardVisuals.checker_diameter / 2)**2 * math.pi * 1

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

    return black_background
