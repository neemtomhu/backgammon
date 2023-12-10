import math

import cv2
import numpy as np

from utils.logger import LOG
from visuals import BoardVisuals
from visuals.BoardVisuals import BackgammonBoardVisuals


def detect_dice_sized_diff(img, min_radius_multiplier, max_radius_multiplier, param2=17):
    x1, y1 = BackgammonBoardVisuals.corners[0][0], BackgammonBoardVisuals.corners[0][1]
    x2, y2 = BackgammonBoardVisuals.corners[3][0], BackgammonBoardVisuals.corners[3][1]
    roi_img = img[y1:y2, x1:x2]

    # Load the image
    gray = cv2.cvtColor(roi_img, cv2.COLOR_BGR2GRAY)

    # Preprocessing
    blurred = cv2.GaussianBlur(gray, (15, 15), 0)

    # Detect circles (potential dice)
    min_radius = int(BoardVisuals.BackgammonBoardVisuals.checker_diameter * min_radius_multiplier)
    max_radius = int(BoardVisuals.BackgammonBoardVisuals.checker_diameter * max_radius_multiplier)
    LOG.debug(f'Min radius: {min_radius}, Max radius: {max_radius}')

    circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT,
                               dp=1.2,
                               minDist=min_radius * 2,
                               param1=50,
                               param2=param2,
                               minRadius=min_radius,
                               maxRadius=max_radius)

    # If circles are detected, add the offset to each circle's coordinates
    if circles is not None:
        img2 = img.copy()
        circles = np.round(circles[0, :]).astype("int")
        for circle in circles:
            circle[0] += x1  # add the x offset
            circle[1] += y1  # add the y offset
            cv2.circle(img2, (circle[0], circle[1]), circle[2], (0, 255, 0), 1)
        # cv2.imshow('Circles', img2)
        # cv2.waitKey(1)
    return img, circles


def detect_dice_value(img, circles):

    if circles is not None:
        dice_values = []

        for (x, y, r) in circles:
            r += 15  # expand the circle to ensure all blobs are properly visible
            # Draw the circle in the output image
            cv2.circle(img, (x, y), r, (0, 255, 0), 1)
            LOG.debug(f"Dice radius: {r}")

            # Extract the ROI
            roi = img[y - r:y + r, x - r:x + r]

            params = cv2.SimpleBlobDetector_Params()
            params.filterByArea = True
            params.minArea = 20  # Adjust as needed
            params.maxArea = 40
            params.filterByCircularity = True
            params.minCircularity = 0.8  # Adjust as needed

            # Create a blob detector with the parameters
            detector = cv2.SimpleBlobDetector_create(params)

            # Detect black blobs on the dice
            blobs_1 = detector.detect(roi)

            if blobs_1:
                LOG.debug(f'Blob size: {math.pi * (blobs_1[0].size / 2.0)**2}')
                # dice_values.append(len(blobs_1))
            # else:
                # Detect white blobs on the dice
            params.blobColor = 255
            detector = cv2.SimpleBlobDetector_create(params)
            blobs_2 = detector.detect(roi)

            keypoints = blobs_1 if len(blobs_1) > len(blobs_2) else blobs_2

            dice_values.append(len(keypoints))

            LOG.info(f'Dice value detected: {len(blobs_1)}')

            # Draw detected blobs on the image
            # Adjust keypoint positions and draw them on the original image
            for keypoint in keypoints:
                adjusted_x = int(keypoint.pt[0] + x - r)
                adjusted_y = int(keypoint.pt[1] + y - r)
                cv2.circle(img, (adjusted_x, adjusted_y), int(keypoint.size), (0, 0, 255), 2)

        dice_values.sort()
        return dice_values

    return []


def preprocess_image(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    return blurred


def detect_blobs(image, blob_color):
    # Set up the SimpleBlobDetector parameters for black or white blobs
    params = cv2.SimpleBlobDetector_Params()
    params.filterByArea = True
    params.minArea = 10
    params.maxArea = 200
    params.filterByCircularity = True
    params.minCircularity = 0.8
    params.filterByConvexity = True
    params.minConvexity = 0.87
    params.filterByInertia = True
    params.minInertiaRatio = 0.01
    params.blobColor = 0 if blob_color == 'black' else 255

    # Create a detector with the parameters
    detector = cv2.SimpleBlobDetector_create(params)

    # Detect blobs
    keypoints = detector.detect(image)
    return keypoints


def draw_blobs(image, keypoints, color):
    # Draw detected blobs as red circles
    for keypoint in keypoints:
        x, y = int(keypoint.pt[0]), int(keypoint.pt[1])
        cv2.circle(image, (x, y), int(keypoint.size / 2), color, 2)


def cluster_keypoints(keypoints, num_clusters=2):
    if len(keypoints) < num_clusters:
        return []

    # Extract the coordinates of the keypoints and convert them to float32
    points = np.float32([[kp.pt[0], kp.pt[1]] for kp in keypoints])

    # Define criteria (type, max_iter, epsilon)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)

    # Apply KMeans clustering
    _, labels, _ = cv2.kmeans(points, num_clusters, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    # Group keypoints by cluster
    clustered_keypoints = [[] for _ in range(num_clusters)]
    for label, keypoint in zip(labels.ravel(), keypoints):
        clustered_keypoints[label].append(keypoint)

    return clustered_keypoints


def draw_clusters(image, clustered_keypoints):
    colors = [(0, 0, 255), (255, 0, 0)]  # Different colors for each dice
    for i, cluster in enumerate(clustered_keypoints):
        for keypoint in cluster:
            x, y = int(keypoint.pt[0]), int(keypoint.pt[1])
            cv2.circle(image, (x, y), int(keypoint.size / 2), colors[i], 2)


def detect_dice(image):
    processed_image = preprocess_image(image)

    # Detect black and white blobs
    black_blobs = detect_blobs(processed_image, 'black')
    white_blobs = detect_blobs(processed_image, 'white')

    # Combine black and white blobs
    all_blobs = black_blobs + white_blobs

    # Cluster the blobs into two groups (assuming two dice)
    clustered_keypoints = cluster_keypoints(all_blobs)

    # Draw clustered blobs on the image
    draw_clusters(image, clustered_keypoints)

    # Count the number of blobs in each cluster to get the dice values
    dice_values = [len(cluster) for cluster in clustered_keypoints]

    # Show the image with detected blobs
    cv2.imshow("Detected Dice", image)
    cv2.waitKey(1)

    return dice_values


def detect_dice_values(img):
    dice_values = []

    # Look fod dice sized changes
    detected_img, circles = detect_dice_sized_diff(
        img,
        min_radius_multiplier=0.3,
        max_radius_multiplier=0.4,
        param2=17)
    if circles is not None:
        LOG.info('Dice roll detected')
        dice_values = detect_dice_value(detected_img, circles)
        # return "Dice roll"
    LOG.debug(f'dice_values: {dice_values}')
    return dice_values
