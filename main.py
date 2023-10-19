import time

import cv2
import tkinter as tk
from tkinter import filedialog

from gameplay.BackgammonGame import BackgammonGame
from utils.dice_value_utils import deduce_dice
from utils.logger import LOG, init_logging
from visuals import BoardVisuals
from visuals.board_detector import detect_backgammon_board
from visuals.checker_detector import count_checkers_on_field, check_for_moved_checkers
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
    # cv2.waitKey(1)

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

        # dice_values, m_from, m_to = detect_movement_type(diff_img)
        dice_values = detect_movement_type(diff_img)
        m_from, m_to = check_for_moved_checkers(next_image)
        moved_from = m_from
        moved_to = m_to
        LOG.info(f'Dice roll: {dice_roll}')

        if dice_values and not dice_roll:
            dice_roll = dice_values
            LOG.info(f'Setting initial dice roll: {dice_roll}')
            # BackgammonGame.get_instance().dice = dice_roll
        elif dice_roll and moved_from and moved_to:
            # LOG.info(f'Making moves: dice_values={dice_roll}, moved_from={moved_from}, moved_to={moved_to}')
            board_state = BackgammonGame.get_instance().board.board
            turn = BackgammonGame.get_instance().turn
            deduced_dice_roll, moved_from, moved_to = deduce_dice(dice_roll, moved_from, moved_to, board_state, turn)
            moved_from.sort(reverse=(turn == -1))
            moved_to.sort(reverse=(turn == -1))

            LOG.info(f'Deduced dice roll: {deduced_dice_roll}, moved_from={moved_from}, moved_to={moved_to}')
            if not deduced_dice_roll:
                # TODO handle/log
                LOG.info(f'Not enough info, moving on, deduced_dice_roll={deduced_dice_roll}')
                anchor_img_pos = next_movement_frame_pos
                continue

            LOG.info(f'Making moves: dice_values={deduced_dice_roll}, moved_from={moved_from}, moved_to={moved_to}')

            # total_movement = abs(sum(moved_from) - sum(moved_to))
            # if total_movement > sum(dice_roll):
            #     dice1 = max(dice_roll)
            #     dice2 = total_movement - dice1
            #     dice_roll = [dice1, dice2]
            #     LOG.info(f'Dice roll: {dice_roll}')
            # elif total_movement < sum(dice_roll):
            #     LOG.info(f'Dice roll: {dice_roll}')
            #     continue

            BackgammonGame.get_instance().set_dice(deduced_dice_roll)
            LOG.info(f'Dice roll: {deduced_dice_roll}')
            while moved_from:
                for f_m in moved_from:
                    for t_m in moved_to:
                        # LOG.info(f'Dice roll: {deduced_dice_roll}')
                        if BackgammonGame.get_instance().make_move(f_m, t_m):
                            moved_from.remove(f_m)
                            moved_to.remove(t_m)
                            LOG.info(f'Dice roll: {deduced_dice_roll}')

            for i in range(25):
                BoardVisuals.BackgammonBoardVisuals.fields[i].checkers = abs(BackgammonGame.get_instance().board.board[i])

            if deduced_dice_roll:
                anchor_img_pos = next_movement_frame_pos
                continue
            # if dice_roll:
            #     dice_roll = sorted(dice_values)
            #     BackgammonGame.get_instance().set_dice(dice_roll)
            # BackgammonGame.get_instance().switch_turn()

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
