import time

import cv2
import tkinter as tk
from tkinter import filedialog

from gameplay.BackgammonGame import BackgammonGame
from utils.logger import LOG, init_logging
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

    init_logging(cap)
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

    dice_roll = []
    moved_from = []
    moved_to = []

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, anchor_img_pos)
        ret, image = cap.read()
        if not ret:
            break

        next_movement_frame_pos = get_next_move_frame(cap, anchor_img_pos)
        cap.set(cv2.CAP_PROP_POS_FRAMES, next_movement_frame_pos)
        ret, next_image = cap.read()
        if not ret:
            break
        cv2.imshow('Next movement', next_image)
        cv2.waitKey(1)
        diff_img = extract_difference(image, next_image)

        dice_values, m_from, m_to = detect_movement_type(diff_img)
        moved_from += m_from
        moved_to += m_to

        if dice_values and not dice_roll:
            dice_roll = dice_values
            LOG.info(f'Setting initial dice roll: {dice_roll}')
            BackgammonGame.get_instance().dice = dice_roll
        elif dice_values:
            LOG.info(f'Making moves')
            for f_m in moved_from:
                for t_m in moved_to:
                    if BackgammonGame.get_instance().make_move(f_m, t_m):
                        moved_from.remove(f_m)
                        moved_to.remove(t_m)

            dice_roll = dice_values.sort()
            BackgammonGame.get_instance().dice = dice_roll

        LOG.info(f'dice_roll={dice_roll}, moved_from={moved_from}, moved_to={moved_to}')

        res = cv2.waitKey(1)
        if res & 0xFF == ord('q'):
            LOG.info('Exiting')
            break
        anchor_img_pos = next_movement_frame_pos

    if detected_img is not None:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
