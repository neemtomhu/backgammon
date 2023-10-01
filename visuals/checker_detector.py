import cv2
import numpy as np

from utils.logger import LOG
from visuals import BoardVisuals


def get_checker_movement(img, circles):
    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Apply thresholding
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    squares = find_squares(thresh)

    movements = []
    for (x, y, r) in circles:
        for square in squares:
            sx, sy, sw, sh = square  # assuming square is a tuple (x, y, width, height)
            if is_circle_in_square((x, y, r), sx, sy, sw, sh):
                cx, cy = get_square_centre(sx, sy, sw, sh)
                field = BoardVisuals.BackgammonBoardVisuals().get_nearest_field_id(cx, cy)
                LOG.info(f'Checker moved to field: {field}')
                movements.append({
                    'circle': (x, y, r),
                    'square': square
                })
        cv2.circle(img, (x, y), r, (0, 255, 0), 1)
    # cv2.imshow('Detected checker movements', img)
    # cv2.waitKey(1)
    # return movements
    return None  # TODO figure out how to return detected changes


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
            squares.append((x, y, w, h))
    LOG.info(f'Squares found: {len(squares)}')
    return squares


def is_circle_in_square(circle, x, y, w, h):
    return x < circle[0] < x + w and y < circle[1] < y + h


def get_square_centre(x, y, w, h):
    x += w/2
    y += h/2
    return x, y

