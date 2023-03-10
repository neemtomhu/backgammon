import cv2
import numpy as np


class BackgammonBoardRecognizer:
    def __init__(self, threshold=200):
        self.threshold = threshold

    def recognize(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, self.threshold, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        board_contour = self._get_board_contour(contours)
        board_frame = self._get_board_frame(frame, board_contour)
        gray_board = cv2.cvtColor(board_frame, cv2.COLOR_BGR2GRAY)
        _, board_thresh = cv2.threshold(gray_board, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return board_thresh

    def _get_board_contour(self, contours):
        areas = [cv2.contourArea(cnt) for cnt in contours]
        max_idx = np.argmax(areas)
        epsilon = 0.1 * cv2.arcLength(contours[max_idx], True)
        approx = cv2.approxPolyDP(contours[max_idx], epsilon, True)
        return approx

    def _get_board_frame(self, frame, contour):
        mask = np.zeros(frame.shape[:2], np.uint8)
        cv2.drawContours(mask, [contour], 0, 255, -1)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray_masked = cv2.bitwise_and(gray, gray, mask=mask)
        board_frame = np.zeros_like(frame)
        board_frame[mask > 0] = frame[mask > 0]
        return board_frame
