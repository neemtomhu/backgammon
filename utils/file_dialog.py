import tkinter as tk
from tkinter import filedialog, messagebox

import cv2

from utils.logger import LOG, init_logging


def ask_for_file_path():
    root = tk.Tk()
    root.withdraw()

    while True:
        file_path = filedialog.askopenfilename(
            title="Select Video file",
            filetypes=[
                ("Video files", "*.mov;*.mp4"),
                ("MOV files", "*.mov"),
                ("MP4 files", "*.mp4"),
            ],
        )

        if file_path:
            return file_path
        else:
            retry = messagebox.askretrycancel(
                "File Selection",
                "No file was selected. Would you like to try again?"
            )
            if not retry:
                return None


def initialize_video_capture(file_path):
    cap = cv2.VideoCapture(file_path)
    if not cap.isOpened():
        LOG.error("Failed to open video file")
        return None

    init_logging(cap)
    return cap
