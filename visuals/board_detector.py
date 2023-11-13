import cv2
import numpy as np
import itertools

from utils.logger import LOG
from utils.utils import draw_group_axes, order_checkers, rotate_input_image_clockwise
from visuals import BoardVisuals


def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


def group_circles_based_on_distance(circles, max_distance):
    LOG.info('Grouping circles on fields')
    processed = set()
    groups = []

    for i, circle in enumerate(circles):
        if i not in processed:
            group = [circle]
            queue = [circle]
            processed.add(i)

            while queue:
                current_circle = queue.pop(0)
                for j, other_circle in enumerate(circles):
                    if j not in processed:
                        if distance(current_circle[:2], other_circle[:2]) <= max_distance:
                            group.append(other_circle)
                            queue.append(other_circle)
                            processed.add(j)

            groups.append(group)

    return groups


def angle_between_lines(line1, line2):
    norm1 = np.linalg.norm(line1)
    norm2 = np.linalg.norm(line2)

    if norm1 == 0 or norm2 == 0:
        return 0

    unit_vector_1 = line1 / norm1
    unit_vector_2 = line2 / norm2
    dot_product = np.dot(unit_vector_1, unit_vector_2)
    angle = np.arccos(dot_product)
    return np.degrees(angle)


def find_opposite_groups(groups, threshold_factor, angle_threshold=15):
    paired_groups = []
    used_indices = set()
    diameters = [circle[2] for group in groups for circle in group]
    median_diameter = np.median(diameters)
    threshold = median_diameter * threshold_factor

    for i, group1 in enumerate(groups):
        if i in used_indices:
            continue

        avg_coord1 = np.mean(group1, axis=0)
        best_match_index = -1
        best_match_diff = float('inf')

        for j, group2 in enumerate(groups):
            if j == i or j in used_indices:
                continue

            avg_coord2 = np.mean(group2, axis=0)
            diff = abs(avg_coord1[1] - avg_coord2[1])

            if diff < best_match_diff:
                line1 = group1[-1] - group1[0]
                line2 = group2[-1] - group2[0]
                angle = angle_between_lines(line1[:2], line2[:2])

                if angle < angle_threshold or abs(angle - 180) < angle_threshold:
                    best_match_diff = diff
                    best_match_index = j

        if best_match_index != -1 and best_match_diff <= threshold:
            paired_groups.append((group1, groups[best_match_index]))
            used_indices.add(i)
            used_indices.add(best_match_index)

    return paired_groups


def color_cluster_size(input_img, x, y, visited):
    if (x, y) in visited:
        return 0

    visited.add((x, y))
    color = input_img[y, x]
    cluster_size = 1

    neighbors = [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if dx != 0 or dy != 0]

    for nx, ny in neighbors:
        if 0 <= nx < input_img.shape[1] and 0 <= ny < input_img.shape[0]:
            if np.array_equal(input_img[ny, nx], color) and (nx, ny) not in visited:
                cluster_size += color_cluster_size(input_img, nx, ny, visited)

    return cluster_size


def draw_circle_groups_pairs(img, group_pairs):
    output = img.copy()
    colors = [(0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    for i, pair in enumerate(group_pairs):
        color = colors[i % len(colors)]
        for j, group in enumerate(pair):
            for circle in group:
                x, y, radius = map(int, circle)
                cv2.circle(output, (x, y), radius, color, 2)

            # Put a number on each group, calculate the position based on the circles in the group
            avg_x = int(sum([circle[0] for circle in group]) / len(group))
            avg_y = int(sum([circle[1] for circle in group]) / len(group))
            cv2.putText(output, str(i + 1), (avg_x, avg_y), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    return output


def get_board_orientation(groups):
    LOG.info('Determining board orientation')
    horizontal_count = 0
    vertical_count = 0

    for group1, group2 in itertools.combinations(groups, 2):
        avg_x1 = np.mean([circle[0] for circle in group1])
        avg_y1 = np.mean([circle[1] for circle in group1])
        avg_x2 = np.mean([circle[0] for circle in group2])
        avg_y2 = np.mean([circle[1] for circle in group2])

        if abs(avg_x1 - avg_x2) < abs(avg_y1 - avg_y2):
            vertical_count += 1
        else:
            horizontal_count += 1

    orientation = "horizontal" if horizontal_count > vertical_count else "vertical"
    LOG.info(f"The board orientation is: {orientation}")

    return orientation


def get_board_corners(paired_groups):
    circle_groups = [group for groups in paired_groups for group in groups]
    all_circles = [circle for group in circle_groups for circle in group]

    # add some padding around the circles
    radius = all_circles[0][2] * 1.3
    LOG.info(f"Adding radius {radius}")

    all_checkers = np.array(all_circles)
    x_min = int(np.min(all_checkers[:, 0]).round() - radius)
    x_max = int(np.max(all_checkers[:, 0]).round() + radius)
    y_min = int(np.min(all_checkers[:, 1]).round() - radius)
    y_max = int(np.max(all_checkers[:, 1]).round() + radius)

    top_left = (x_min, y_min)
    top_right = (x_max, y_min)
    bottom_left = (x_min, y_max)
    bottom_right = (x_max, y_max)
    LOG.info(f'Corners: {top_left, top_right, bottom_left, bottom_right}')

    return top_left, top_right, bottom_left, bottom_right


def draw_rectangle(input_img, corners):
    img = input_img.copy()
    return cv2.rectangle(img, (corners[0]), (corners[3]), (0, 255, 0), 2)


def detect_backgammon_board(input_img):
    BoardVisuals.BackgammonBoardVisuals.initialize((0, 0), "vertical")

    LOG.info('Detecting board')

    input_img = rotate_if_needed(input_img)
    closed = get_closed_image(input_img)
    predicted_radius = predict_checker_diameter(closed)
    circles = find_circles(closed, predicted_radius)
    radii = [circle[2] for circle in circles[0]]
    diameters = [2 * radius for radius in radii]
    median_diameter = np.median(diameters)
    BoardVisuals.BackgammonBoardVisuals.checker_diameter = median_diameter
    LOG.info(f'Median checker diameter: {median_diameter}')

    # Calculate max_distance as a function of the median diameter
    max_distance = median_diameter * 1.2  # Adjust the multiplier as needed

    groups = group_circles_based_on_distance(circles[0], max_distance)

    # Draw the detected circles on a copy of the input image
    detected_img = input_img.copy()
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            cv2.circle(detected_img, (i[0], i[1]), i[2], (0, 255, 0), 2)
    # cv2.imshow('Circles', detected_img)

    # orientation = get_board_orientation(groups)
    paired_groups = find_opposite_groups(groups, 5)
    ordered_paired_groups = order_checkers(paired_groups)

    # BoardVisuals.BackgammonBoardVisuals.orientation = orientation
    paired_groups_image = draw_circle_groups_pairs(input_img, ordered_paired_groups)
    BoardVisuals.BackgammonBoardVisuals.corners = get_board_corners(paired_groups)
    detected_board_image = draw_rectangle(paired_groups_image, BoardVisuals.BackgammonBoardVisuals.corners)
    detected_img = draw_group_axes(detected_board_image, ordered_paired_groups)
    LOG.info('Board detected')
    # cv2.imshow('Detected board', detected_img)
    # cv2.waitKey(1)

    return detected_img


def rotate_if_needed(input_img):
    if input_img.shape[0] < input_img.shape[1]:
        return rotate_input_image_clockwise(input_img)
    LOG.info(f'Input image height: {input_img.shape[0]}, width: {input_img.shape[1]}')
    return input_img


def predict_checker_diameter(closed):
    circles = cv2.HoughCircles(closed, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=25, param2=35, minRadius=12,
                               maxRadius=29)
    radii = [circle[2] for circle in circles[0]]
    return np.median(radii)


def find_circles(img, predicted_radius, param1=25, param2=24):
    min_dist = int(predicted_radius * 1.8)
    min_radius = int(predicted_radius * 0.76)
    max_radius = int(predicted_radius * 1.25)
    # edges = cv2.Canny(img, 50, 150)
    # cv2.imshow('Edges', edges)
    # cv2.waitKey(1)
    return cv2.HoughCircles(img, cv2.HOUGH_GRADIENT, dp=1,
                            minDist=min_dist,
                            param1=param1,
                            param2=param2,
                            minRadius=min_radius,
                            maxRadius=max_radius)


def convert_to_gray(input_img):
    return cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)


def apply_clahe(gray):
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def preprocess_image(contrast_enhanced):
    blurred = cv2.GaussianBlur(contrast_enhanced, (5, 5), 0)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    return cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)


def preprocess_image_for_checker_detection(input_img):
    gray = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Apply morphological opening
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opening = cv2.morphologyEx(blurred, cv2.MORPH_OPEN, kernel)

    # Apply dilation
    dilated = cv2.dilate(opening, kernel, iterations=1)

    # Apply adaptive thresholding
    thresh = cv2.adaptiveThreshold(dilated, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    edges = cv2.Canny(thresh, 100, 200)
    return edges


def get_closed_image(input_img):
    gray = convert_to_gray(input_img)
    contrast_enhanced = apply_clahe(gray)
    return preprocess_image(contrast_enhanced)
