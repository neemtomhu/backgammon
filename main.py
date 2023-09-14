import cv2
import tkinter as tk
from tkinter import filedialog

from utils.logger import LOG
from visuals.board_detector import detect_backgammon_board
from visuals.dicedetection.dice_detector import detect_dice


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
    ret, frame = cap.read()

    skip_frames = 10

    image = frame.copy()
    detected_img = detect_backgammon_board(image)

    while True:
        ret, image = cap.read()

        if not ret:
            break
        detect_dice(image)
        res = cv2.waitKey(1)
        if res & 0xFF == ord('q'):
            LOG.info('Exiting')
            break

        current_position = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
        LOG.info(f"Current pos: {current_position}")
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_position + skip_frames)

    if detected_img is not None:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
