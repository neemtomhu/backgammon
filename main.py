import cv2
import tkinter as tk
from tkinter import filedialog
from backgammon_board_recognizer import BackgammonBoardRecognizer

# Create a Tkinter root window
root = tk.Tk()
root.withdraw()

# Get the path to the MOV file using a file dialog
file_path = filedialog.askopenfilename(title="Select MOV file", filetypes=[("MOV files", "*.mov")])

# Create a video capture object and read the first frame
cap = cv2.VideoCapture(file_path)
ret, frame = cap.read()

# Define the region of interest (ROI) for the backgammon board
board_roi = (300, 100, 400, 400)

# Create a backgammon board recognizer object
board_recognizer = BackgammonBoardRecognizer(threshold=100)

# Create a window to display the video
cv2.namedWindow("Video", cv2.WINDOW_NORMAL)

# Set up play/pause controls
paused = False
while ret:
    # If not paused, recognize the backgammon board in the current frame
    if not paused:
        frame = board_recognizer.recognize(frame)

    # Display the frame in the window
    cv2.imshow("Video", frame)

    # Wait for a key press to advance to the next frame, pause/unpause, or exit
    key = cv2.waitKey(1)
    if key == ord('q'):
        break
    elif key == ord(' '):
        paused = not paused

    # If paused, wait for spacebar to unpause
    while paused:
        key = cv2.waitKey(1)
        if key == ord('q'):
            break
        elif key == ord(' '):
            paused = False

    ret, frame = cap.read()

# Release the video capture object and close the window
cap.release()
cv2.destroyAllWindows()
