import cv2
import numpy as np

from utils.logger import LOG
from visuals import BoardVisuals
from visuals.board_detector import get_closed_image, find_circles, preprocess_image_for_checker_detection


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
