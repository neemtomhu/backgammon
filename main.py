import cv2
import tkinter as tk
from tkinter import filedialog
from board_detector import detect_backgammon_board
from utils.logger import LOG


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

    image = frame.copy()
    detected_img, roi = detect_backgammon_board(image)

    if roi is not None:
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
