import cv2
import numpy as np
import itertools
from utils.logger import init_logging


def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def group_circles_based_on_distance(circles, max_distance):
    LOG.info('Grouping circles')
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


def find_opposite_groups(groups, orientation, threshold_factor):
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

            if orientation == "horizontal":
                diff = abs(avg_coord1[0] - avg_coord2[0])
            else:
                diff = abs(avg_coord1[1] - avg_coord2[1])

            if diff < best_match_diff:
                best_match_diff = diff
                best_match_index = j

        if best_match_index != -1 and best_match_diff <= threshold:
            paired_groups.append((group1, groups[best_match_index]))
            used_indices.add(i)
            used_indices.add(best_match_index)

    return paired_groups


def find_missing_checkers(paired_groups, input_img):
    for group1, group2 in paired_groups:
        count1 = len(group1)
        count2 = len(group2)

        if count1 != count2:
            LOG.info(f"Checker count mismatch: {count1} vs {count2}")
            # Implement your strategy to find missing checkers here
            # For example, you can use a different set of parameters for HoughCircles
            # or try other image processing techniques to detect missing checkers
            missing_checkers = find_missing_checkers_using_heuristics(input_img, group1, group2)
            # Update the groups with the found checkers
            if missing_checkers:
                if count1 < count2:
                    group1.extend(missing_checkers)
                else:
                    group2.extend(missing_checkers)
                LOG.info(f"Found {len(missing_checkers)} missing checkers")

    return paired_groups


def find_missing_checkers_using_heuristics(input_img, group1, group2):
    missing_checkers = []

    # Determine which group has fewer checkers and calculate the average position of checkers
    if len(group1) < len(group2):
        smaller_group = group1
        larger_group = group2
    else:
        smaller_group = group2
        larger_group = group1

    avg_x = int(np.mean([circle[0] for circle in smaller_group]))
    avg_y = int(np.mean([circle[1] for circle in smaller_group]))

    # Get the color of the missing checkers
    x, y, _ = smaller_group[0]
    x, y = int(x), int(y)  # Add this line to convert x and y to integers
    checker_color = input_img[y, x]

    missing_checkers = search_for_missing_checkers(input_img, checker_color, avg_x, avg_y)

    LOG.info(f"Missing checker found: {len(missing_checkers)}")
    return missing_checkers


def search_for_missing_checkers(input_img, checker_color, avg_x, avg_y):
    missing_checkers = []
    visited = set()

    search_radius = 50
    x_min = max(0, avg_x - search_radius)
    x_max = min(input_img.shape[1] - 1, avg_x + search_radius)
    y_min = max(0, avg_y - search_radius)
    y_max = min(input_img.shape[0] - 1, avg_y + search_radius)

    for y in range(y_min, y_max):
        for x in range(x_min, x_max):
            if np.array_equal(input_img[y, x], checker_color) and (x, y) not in visited:
                cluster_size = color_cluster_size(input_img, x, y, visited)

                # Customize the cluster size threshold to match the expected size of a checker
                if cluster_size > 30:  # Adjust this threshold as needed
                    missing_checkers.append((x, y, 15))  # Assuming a fixed radius for missing checkers

    return missing_checkers


def color_cluster_size(input_img, x, y, visited, threshold=0.8):
    if (x, y) in visited:
        return 0

    visited.add((x, y))
    color = input_img[y, x]
    cluster_size = 1

    neighbors = [(x + dx, y + dy) for dx in [-1, 0, 1] for dy in [-1, 0, 1] if dx != 0 or dy != 0]

    for nx, ny in neighbors:
        if 0 <= nx < input_img.shape[1] and 0 <= ny < input_img.shape[0]:
            if np.array_equal(input_img[ny, nx], color) and (nx, ny) not in visited:
                cluster_size += color_cluster_size(input_img, nx, ny, visited, threshold)

    return cluster_size


def draw_circle_groups_pairs(img, group_pairs):
    output = img.copy()
    colors = [(0, 255, 0), (0, 0, 255), (255, 0, 0), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

    for i, pair in enumerate(group_pairs):
        color = colors[i % len(colors)]
        for group in pair:
            for circle in group:
                x, y, radius = map(int, circle)
                cv2.circle(output, (x, y), radius, color, 2)

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

    return "horizontal" if horizontal_count > vertical_count else "vertical"


def draw_roi_rectangle(input_img, paired_groups):
    circle_groups = [group for groups in paired_groups for group in groups]
    all_circles = [circle for group in circle_groups for circle in group]
    radius = all_circles[0][2] * 1.3
    LOG.info(f"Adding radius {radius}")

    all_checkers = np.array(all_circles)
    x_min = int(np.min(all_checkers[:, 0]).round() - radius)
    x_max = int(np.max(all_checkers[:, 0]).round() + radius)
    y_min = int(np.min(all_checkers[:, 1]).round() - radius)
    y_max = int(np.max(all_checkers[:, 1]).round() + radius)
    cv2.rectangle(input_img, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)


def detect_backgammon_board(input_img):
    # Convert the image to grayscale
    gray = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)

    # Apply CLAHE to enhance the contrast
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast_enhanced = clahe.apply(gray)

    # Apply a Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(contrast_enhanced, (5, 5), 0)

    # Apply morphological closing to fill gaps in circles
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    closed = cv2.morphologyEx(blurred, cv2.MORPH_CLOSE, kernel)

    # edges = cv2.Canny(closed, 50, 150)
    # cv2.imshow('Edges', edges)

    # Use the Hough Circle Transform to find circles
    circles = cv2.HoughCircles(closed, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=50, param2=30, minRadius=10, maxRadius=30)
    radii = [circle[2] for circle in circles[0]]
    diameters = [2 * radius for radius in radii]
    median_diameter = np.median(diameters)

    # Calculate max_distance as a function of the median diameter
    max_distance = median_diameter * 1.3  # Adjust the multiplier as needed

    groups = group_circles_based_on_distance(circles[0], max_distance)

    # Draw the detected circles on a copy of the input image
    detected_img = input_img.copy()
    if circles is not None:
        circles = np.uint16(np.around(circles))
        for i in circles[0, :]:
            cv2.circle(detected_img, (i[0], i[1]), i[2], (0, 255, 0), 2)

    orientation = get_board_orientation(groups)
    LOG.info(f"The board orientation is: {orientation}")

    threshold_factor = 5
    paired_groups = find_opposite_groups(groups, orientation, threshold_factor)
    paired_groups_image = draw_circle_groups_pairs(input_img, paired_groups)
    draw_roi_rectangle(paired_groups_image, paired_groups)
    cv2.imshow("Circle groups", paired_groups_image)
    cv2.imshow("ROI", input_img)
    find_missing_checkers(paired_groups, input_img)

    return detected_img


if __name__ == "__main__":
    LOG = init_logging()
    input_img1 = cv2.imread("/Users/geri/Desktop/MSc/diploma/project/Screenshot1.png")
    LOG.info('Opened image')
    detected_img = detect_backgammon_board(input_img1)
    cv2.imshow("Detected Backgammon Board", detected_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
