import cv2
import numpy as np

# Global variables
# updated_roi = None
roi_corners = None
dragging = False
active_corner = -1


def mouse_callback(event, x, y, flags, param):
    global roi_corners, dragging, active_corner

    if event == cv2.EVENT_LBUTTONDOWN:
        for i, corner in enumerate(roi_corners):
            if abs(corner[0] - x) < 10 and abs(corner[1] - y) < 10:
                dragging = True
                active_corner = i
                break

    if event == cv2.EVENT_MOUSEMOVE and dragging:
        roi_corners[active_corner] = (x, y)
        # roi_corners[active_corner + 2] = (roi_corners[active_corner])

    if event == cv2.EVENT_LBUTTONUP:
        dragging = False
        active_corner = -1


def get_roi(image, largest_rect, second_largest_rect):
    global updated_roi, roi_corners

    # Create the initial ROI
    x_min = min(largest_rect[0], second_largest_rect[0])
    y_min = min(largest_rect[1], second_largest_rect[1])
    x_max = max(largest_rect[0] + largest_rect[2], second_largest_rect[0] + second_largest_rect[2])
    y_max = max(largest_rect[1] + largest_rect[3], second_largest_rect[1] + second_largest_rect[3])

    roi_corners = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]

    # Create a window and set the mouse callback function
    cv2.namedWindow("Update detected area if necessary - press Q to finnish")
    cv2.setMouseCallback("Update detected area if necessary - press Q to finnish", mouse_callback)

    # Display the initial ROI with draggable vertices
    while True:
        updated_roi = image.copy()
        print(roi_corners)
        for i in range(4):
            cv2.line(updated_roi, roi_corners[i], roi_corners[(i + 1) % 4], (0, 255, 0), 2)
            # cv2.rectangle(updated_roi, roi_corners[1], (roi_corners[])) TODO keep rectangle
            cv2.circle(updated_roi, roi_corners[i], 5, (0, 0, 255), -1)

        cv2.imshow("Update detected area if necessary - press Q to finnish", updated_roi)
        key = cv2.waitKey(1) & 0xFF

        if key == ord("q"):
            break

    cv2.destroyAllWindows()

    # Crop the final ROI
    x_min = min([point[0] for point in roi_corners])
    x_max = max([point[0] for point in roi_corners])
    y_min = min([point[1] for point in roi_corners])
    y_max = max([point[1] for point in roi_corners])

    cropped_roi = updated_roi[y_min:y_max, x_min:x_max]

    return cropped_roi


def detect_board_area(image):
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    lower_green = np.array([40, 30, 30])
    upper_green = np.array([90, 255, 180])

    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    green_mask = cv2.bitwise_not(green_mask)  # Invert the mask to get the area of interest

    _, thresh = cv2.threshold(green_mask, 60, 255, cv2.THRESH_BINARY_INV)
    thresh = cv2.GaussianBlur(thresh, (5, 5), 0)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    areas = [cv2.contourArea(cnt) for cnt in contours]
    sorted_contours = sorted(zip(areas, contours), key=lambda x: x[0], reverse=True)

    largest_rect = None
    second_largest_rect = None

    if len(sorted_contours) >= 2:
        # Draw and store the largest rectangle
        area, cnt = sorted_contours[0]
        x1, y1, w1, h1 = cv2.boundingRect(cnt)
        largest_rect = (x1, y1, w1, h1)
        # cv2.rectangle(image, (x1, y1), (x1 + w1, y1 + h1), (0, 255, 0), 2)

        # Draw and store the second-largest rectangle
        _, cnt2 = sorted_contours[1]
        x2, y2, _, h2 = cv2.boundingRect(cnt2)
        second_largest_rect = (x1, y2, w1, h2)
        # cv2.rectangle(image, (x1, y2), (x1 + w1, y2 + h2), (0, 255, 0), 2)

    return largest_rect, second_largest_rect
