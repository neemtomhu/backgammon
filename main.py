import cv2
import tkinter as tk
from tkinter import filedialog
from board_detector import detect_board_area, get_roi


class BoardData:
    roi = None


def main():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename(title="Select MOV file", filetypes=[("MOV files", "*.mov")])

    cap = cv2.VideoCapture(file_path)
    ret, frame = cap.read()

    image = frame.copy()
    largest_rect, second_largest_rect = detect_board_area(image)
    roi = get_roi(image, largest_rect, second_largest_rect)

    if roi is not None:
        BoardData.roi = roi
        cv2.imshow("ROI", roi)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
