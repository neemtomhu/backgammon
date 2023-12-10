import cv2
import numpy as np

from utils.logger import LOG
from visuals import BoardVisuals
from visuals.board_detector import get_closed_image, find_circles, preprocess_image_for_checker_detection


def get_checker_movement(img, circles):
    moved_from = []
    moved_to = []
    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    squares = find_squares(thresh)

    for square in squares:
        sx, sy, sw, sh = square  # assuming square is a tuple (x, y, width, height)
        circle_found = False  # flag to keep track of whether a circle was found in this square
        for (x, y, r) in circles:
            if is_circle_in_square((x, y, r), sx, sy, sw, sh):
                circle_found = True  # set the flag to True since a circle was found
                # cx, cy = get_square_centre(sx, sy, sw, sh)
                field = BoardVisuals.BackgammonBoardVisuals().get_nearest_field_id(x, y)
                LOG.info(f'Checker moved to field: {field}')
                moved_to.append(field)
                cv2.circle(img, (x, y), r, (0, 255, 0), 1)
        if not circle_found:
            field = BoardVisuals.BackgammonBoardVisuals().get_nearest_field_id(sx, sy)
            LOG.info(f'Checker moved from field: {field}')
            moved_from.append(field)
    # cv2.imshow('Detected checker movements', img)
    # cv2.waitKey(1)
    # return movements
    return moved_from, moved_to


def find_squares(thresh_img):
    # Find contours in the thresholded image
    contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    squares = []
    for contour in contours:
        # Approximate the contour by a polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # If the polygon has 4 vertices, it is considered as a square
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter out squares that are smaller than a checker
            threshold_diameter = BoardVisuals.BackgammonBoardVisuals.checker_diameter * 0.9
            if w > threshold_diameter and h > threshold_diameter:
                squares.append((x, y, w, h))
    LOG.info(f'Squares found: {len(squares)}')
    return squares


def is_circle_in_square(circle, x, y, w, h):
    return x < circle[0] < x + w and y < circle[1] < y + h


def get_square_centre(x, y, w, h):
    x += w/2
    y += h/2
    return x, y


def count_checkers_on_field(img, field):
    checker_diameter = BoardVisuals.BackgammonBoardVisuals.checker_diameter
    offset = checker_diameter * 0.75

    x1, x2 = sorted([int(field.endpoints[0]), int(field.endpoints[2])])
    y1, y2 = sorted([int(field.endpoints[1] - offset), int(field.endpoints[3] + offset)])
    roi = img[y1:y2, x1:x2]
    # cv2.imshow('Field ROI', roi)
    # cv2.waitKey(1)
    closed = get_closed_image(roi)
    # cv2.imshow(f'Closed roi', closed)
    # cv2.waitKey(1)
    checkers = find_circles(closed, checker_diameter / 2, param1=200, param2=18)
    filtered_circles = []
    if checkers is not None:
        circles = np.uint16(np.around(checkers))

        # Filter circles whose centers are outside the ROI
        for circle in circles[0, :]:
            # Convert circle's origin back to original image coordinates
            circle_x = circle[0] + x1
            circle_y = circle[1] + y1

            nearest_field_id = BoardVisuals.BackgammonBoardVisuals().get_nearest_field_id(circle_x, circle_y)
            if nearest_field_id == field.field_number or nearest_field_id == 0:
                filtered_circles.append(circle)

        for i in filtered_circles:
            cv2.circle(closed, (i[0], i[1]), i[2], (0, 255, 0), 2)

    result = len(filtered_circles) if checkers is not None else 0
    LOG.debug(f'Checkers found on field [{field.field_number}]: {result}')

    if result != field.checkers:
        cv2.imshow(f'Detected checkers on field {field.field_number}', closed)
        cv2.waitKey(1)
    return result


def check_for_moved_checkers(img):
    moved_from = []
    moved_to = []
    for i in range(0, 25):
        LOG.debug(f'Counting checkers on field {i}')
        field = BoardVisuals.BackgammonBoardVisuals.fields[i]
        current_count = count_checkers_on_field(img, BoardVisuals.BackgammonBoardVisuals.fields[i])

        if current_count < field.checkers:
            LOG.info(f'Checker moved from field {i}, previous: {field.checkers}, current: {current_count}')
            moved_from.extend([i] * abs(field.checkers - current_count))
        elif current_count > field.checkers:
            LOG.info(f'Checker moved to field {i}, previous: {field.checkers}, current: {current_count}')
            moved_to.extend([i] * abs(field.checkers - current_count))

    return moved_from, moved_to


def bearing_off(board_state):
    return sum(abs(x) for x in board_state) < 30
