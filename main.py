import time
import uuid
import webbrowser
from threading import Thread

import cv2
from werkzeug import run_simple

import utils.globals as globals
from gameplay.BackgammonGame import BackgammonGame
from ui_app.app import file_mappings, app
from utils.dice_value_utils import deduce_dice
from utils.file_dialog import ask_for_file_path, initialize_video_capture
from utils.logger import LOG
from visuals import BoardVisuals
from visuals.BoardVisuals import BackgammonBoardVisuals
from visuals.board_detector import detect_backgammon_board
from visuals.checker_detector import check_for_moved_checkers, bearing_off
from visuals.dicedetection.dice_detector import detect_dice
from visuals.movement_diff import get_anchor_frame, get_next_move_frame, extract_difference

FRAMES_TO_SKIP_INITIAL = 19
AREA_THRESHOLD_INITIAL = 1000
AREA_THRESHOLD_BEARING_OFF = 20000
FRAMES_TO_SKIP_BEARING_OFF = 2
FRAMES_TO_SKIP_STANDARD = 4


def main():
    file_path = ask_for_file_path()

    cap = initialize_video_capture(file_path)

    # display_results(file_path)

    starting_frame_pos = get_anchor_frame(cap)

    cap.set(cv2.CAP_PROP_POS_FRAMES, starting_frame_pos)
    ret, image = cap.read()
    fps = cap.get(cv2.CAP_PROP_FPS)
    detected_img = detect_backgammon_board(image)
    board_roi = BackgammonBoardVisuals.corners

    cv2.imshow('Detected board', detected_img)
    cv2.waitKey(1)

    anchor_img_pos = starting_frame_pos
    globals.last_move_time = get_time_from_frame_pos(anchor_img_pos, fps)
    LOG.info(f'Last Move time: {globals.last_move_time}')
    LOG.info(f'anchor_img_pos={anchor_img_pos}')

    frames_to_skip = FRAMES_TO_SKIP_INITIAL
    area_thresh = AREA_THRESHOLD_INITIAL
    board_state = BackgammonGame.get_instance().board.board

    is_first_move = True
    dice_roll = []
    moved_from = []
    moved_to = []

    while True:

        if bearing_off(board_state):
            if sum(abs(x) for x in board_state) < 16:
                frames_to_skip = FRAMES_TO_SKIP_BEARING_OFF
                area_thresh = AREA_THRESHOLD_BEARING_OFF
            else:
                frames_to_skip = FRAMES_TO_SKIP_STANDARD

        cap.set(cv2.CAP_PROP_POS_FRAMES, anchor_img_pos)
        LOG.debug(f'anchor_img_pos={get_time_from_frame_pos(anchor_img_pos, fps)}')
        ret, image = cap.read()
        if not ret:
            break

        # Collect all the movements from the player in turn
        turn = BackgammonGame.get_instance().turn
        prev_move_pos = anchor_img_pos
        while True:
            LOG.debug(f'prev_move_pos={get_time_from_frame_pos(prev_move_pos, fps)}')

            if not moved_from:
                LOG.info(f'Checking for moved checkers')
                moved_from, moved_to = check_for_moved_checkers(image)

            if moved_from and 0 in moved_to:
                for m_t in moved_to:
                    if BackgammonGame.get_instance().board.board[m_t] * turn == -1:
                        moved_to.append(m_t)
                        break

                for m_f in moved_from:
                    if BackgammonGame.get_instance().board.board[m_f] * turn == -1 and m_f not in moved_to:
                        moved_to.append(m_f)

            if bearing_off(board_state):
                moved_from = [m for m in moved_from if board_state[m] * turn > 0]

            next_movement_frame_pos = get_next_move_frame(cap, prev_move_pos, board_roi, area_thresh=area_thresh, frames_to_skip=frames_to_skip)

            LOG.info(f'next_movement_frame_pos={get_time_from_frame_pos(next_movement_frame_pos, fps)}')
            ret, next_image = cap.read()
            if not ret:
                break

            diff_img = extract_difference(image, next_image)


            dice_values = detect_dice(diff_img)

            if dice_values and not dice_roll:
                dice_roll = dice_values
                LOG.info(f'Setting initial dice roll: {dice_roll}')
                # BackgammonGame.get_instance().dice = dice_roll

            # identify the starting player
            if is_first_move and moved_from and moved_from[0] > 12:
                turn = -1
                BackgammonGame.get_instance().set_turn(turn)
                is_first_move = False

            next_moved_from, next_moved_to = check_for_moved_checkers(next_image)

            # for pos in moved_from:
            #     if pos not in next_moved_from:
            #         moved_from.remove(pos)

            if not next_moved_from:
                prev_move_pos = next_movement_frame_pos
                continue

            if next_moved_from == moved_from and next_moved_to == moved_to:
                prev_move_pos = next_movement_frame_pos
                continue

            if not moved_from:
                prev_move_pos = next_movement_frame_pos
                moved_from = next_moved_from
                moved_to = next_moved_to
                continue

            if 0 in moved_to and 0 not in next_moved_to:
                LOG.info(f'Opponents move detected from bar, braking')
                break

            new_move_from = [i for i in next_moved_from if i not in moved_from]
            new_moved_to = [i for i in next_moved_to if i not in moved_to]
            if new_move_from and 0 in new_moved_to:
                for m_f in moved_from:
                    if BackgammonGame.get_instance().board.board[m_f] * turn == -1:
                        moved_to.append(m_f)
                # moved_to.append(new_move_from[0])
                # moved_to.remove(0)

            opponent_moved = False
            for m_f in new_move_from:
                if 0 in new_moved_to and BackgammonGame.get_instance().board.board[m_f] * turn == -1:
                    continue
                if BackgammonGame.get_instance().board.board[m_f] * turn < 0:
                    LOG.info(f'Opponents move detected, braking')
                    opponent_moved = True
                    break
            if opponent_moved:
                break

            prev_move_pos = next_movement_frame_pos
            moved_from = next_moved_from
            moved_to = next_moved_to

        LOG.info(f'Detected dice roll: {dice_roll}, moved_from={moved_from}, moved_to={moved_to}')

        board_state = BackgammonGame.get_instance().board.board

        deduced_dice_roll, moved_from, moved_to = deduce_dice(dice_roll, moved_from, moved_to, board_state, turn)
        moved_from.sort(reverse=(turn == -1))
        moved_to.sort(reverse=(turn == -1))

        if deduced_dice_roll == dice_roll:
            LOG.info('Correct dice roll detected')

        LOG.info(f'Deduced dice roll: {deduced_dice_roll}, moved_from={moved_from}, moved_to={moved_to}')
        if not deduced_dice_roll:
            LOG.info(f'Not enough info, moving on, deduced_dice_roll={deduced_dice_roll}')
            anchor_img_pos = next_movement_frame_pos
            continue

        LOG.info(f'Making moves: dice_values={deduced_dice_roll}, moved_from={moved_from}, moved_to={moved_to}')

        BackgammonGame.get_instance().set_dice(deduced_dice_roll)

        while moved_from:
            for f_m in moved_from:
                for t_m in moved_to:
                    LOG.info(f'Dice roll: {deduced_dice_roll}')
                    if BackgammonGame.get_instance().make_move(f_m, t_m):
                        moved_from.remove(f_m)
                        moved_to.remove(t_m)
                        # LOG.info(f'Dice roll: {deduced_dice_roll}')

        for i in range(25):
            BoardVisuals.BackgammonBoardVisuals.fields[i].checkers = abs(BackgammonGame.get_instance().board.board[i])

        BoardVisuals.BackgammonBoardVisuals.fields[0].checkers += abs(BackgammonGame.get_instance().board.board[25])

        if all(x <= 0 for x in BackgammonGame.get_instance().board.board):
            LOG.info('Game finished, player 1 wins')
            cv2.destroyAllWindows()
            cap.release()
            display_results(file_path)
            break
        elif all(x >= 0 for x in BackgammonGame.get_instance().board.board):
            LOG.info('Game finished, player -1 wins')
            cv2.destroyAllWindows()
            cap.release()
            display_results(file_path)
            break

        if deduced_dice_roll:
            anchor_img_pos = next_movement_frame_pos
            continue

        LOG.info(f'dice_roll={dice_roll}, moved_from={moved_from}, moved_to={moved_to}')

        res = cv2.waitKey(1)
        if res & 0xFF == ord('q'):
            LOG.info('Exiting')
            break
        anchor_img_pos = prev_move_pos
        globals.last_move_time = get_time_from_frame_pos(anchor_img_pos, fps)

    if detected_img is not None:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


def get_time_from_frame_pos(pos, fps):
    # Calculate total seconds
    total_seconds = int(pos / fps)

    # Convert total seconds to minutes and seconds
    minutes = total_seconds // 60
    seconds = total_seconds % 60

    # Return in mm:ss format
    return f"{minutes:02}:{seconds:02}"


def start_server():
    run_simple('127.0.0.1', 5000, app, use_reloader=False, use_debugger=True)


def display_results(file_path):
    server_thread = Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

    token = str(uuid.uuid4())
    file_path = file_path.replace('/', '\\')
    file_mappings[token] = file_path

    # Open a browser window with the processed video
    webbrowser.open(f'http://127.0.0.1:5000/view-video/{token}')
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        server_thread.join()


if __name__ == "__main__":
    main()
