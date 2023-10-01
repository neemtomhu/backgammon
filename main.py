import time

import cv2
import tkinter as tk
from tkinter import filedialog

from utils.logger import LOG
from visuals.board_detector import detect_backgammon_board
from visuals.dicedetection.dice_detector import detect_dice_value, detect_dice_sized_diff
from visuals.movement_diff import highlight_diff, get_anchor_frame, get_next_move_frame, extract_difference, \
    detect_movement_type


class BoardData:
    roi = None


def main():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(
        title="Select Video file",
        filetypes=[
            ("Video files", "*.mov;*.mp4"),
            ("MOV files", "*.mov"),
            ("MP4 files", "*.mp4"),
        ],
    )

    cap = cv2.VideoCapture(file_path)
    # ret, frame = cap.read()

    skip_frames = 100

    starting_frame_pos = get_anchor_frame(cap)
    cap.set(cv2.CAP_PROP_POS_FRAMES, starting_frame_pos)
    ret, image = cap.read()
    detected_img = detect_backgammon_board(image)

    # cv2.imshow('Detected board', detected_img)
    cv2.waitKey(1)

    next_movement_frame_pos = get_next_move_frame(cap, starting_frame_pos)
    cap.set(cv2.CAP_PROP_POS_FRAMES, next_movement_frame_pos)
    ret, next_image = cap.read()
    # cv2.imshow('Next move', next_image)
    # cv2.waitKey(1)

    # diff_img = highlight_diff(image, next_image)
    diff_img = extract_difference(image, next_image)
    detect_movement_type(diff_img)

    anchor_img_pos = starting_frame_pos

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, anchor_img_pos)
        ret, image = cap.read()

        if not ret:
            break
        next_movement_frame_pos = get_next_move_frame(cap, anchor_img_pos)
        cap.set(cv2.CAP_PROP_POS_FRAMES, next_movement_frame_pos)
        ret, next_image = cap.read()
        # cv2.imshow('Next movement', next_image)
        # cv2.waitKey(1)
        diff_img = extract_difference(image, next_image)

        detect_movement_type(diff_img)

        res = cv2.waitKey(1)
        if res & 0xFF == ord('q'):
            LOG.info('Exiting')
            break

        anchor_img_pos = next_movement_frame_pos
        # time.sleep(30)

        # current_position = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        # LOG.info(f"Current pos: {current_position}")
        #
        # cap.set(cv2.CAP_PROP_POS_FRAMES, current_position + skip_frames)
        # ret, image2 = cap.read()
        #
        # if not ret:
        #     break
        #
        # highlight_diff(image, image2)

    if detected_img is not None:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
