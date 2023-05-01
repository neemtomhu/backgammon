import cv2
import numpy as np
import itertools
from sklearn.cluster import KMeans

# def detect_backgammon_board(input_img):
#     gray = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)
#     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#     edges = cv2.Canny(blurred, 50, 200)
#
#     # Detect lines using Hough Line Transform
#     lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 100, minLineLength=100, maxLineGap=10)
#
#     if lines is not None:
#         for line in lines:
#             x1, y1, x2, y2 = line[0]
#             cv2.line(input_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
#
#     return input_img


# def get_lines_intersection(line1, line2):
#     rho1, theta1 = line1
#     rho2, theta2 = line2
#     A = np.array([
#         [np.cos(theta1), np.sin(theta1)],
#         [np.cos(theta2), np.sin(theta2)]
#     ])
#     b = np.array([[rho1], [rho2]])
#
#     if np.abs(np.linalg.det(A)) > 1e-5:
#         x0, y0 = np.linalg.solve(A, b)
#         x0, y0 = int(np.round(x0)), int(np.round(y0))
#         return [x0, y0]
#     else:
#         return None
#
#
# def detect_backgammon_board(input_img):
#     gray = cv2.cvtColor(input_img, cv2.COLOR_BGR2GRAY)
#     blurred = cv2.GaussianBlur(gray, (5, 5), 0)
#     edges = cv2.Canny(blurred, 50, 200)
#
#     cv2.imshow('edges', edges)
#
#     lines = cv2.HoughLines(edges, 1, np.pi / 180, 100)
#
#     if lines is not None:
#         # Cluster lines based on their angles
#         angles = np.array([line[0][1] for line in lines])
#         kmeans = KMeans(n_clusters=2, random_state=0).fit(angles.reshape(-1, 1))
#         labels = kmeans.labels_
#
#         # Find parallel line pairs
#         parallel_line_pairs = []
#         for label in np.unique(labels):
#             label_indices = np.where(labels == label)[0]
#             label_lines = lines[label_indices]
#             sorted_lines = sorted(label_lines, key=lambda x: x[0][0], reverse=True)
#             for i in range(len(sorted_lines) - 1):
#                 line1 = sorted_lines[i]
#                 line2 = sorted_lines[i + 1]
#                 parallel_line_pairs.append((line
def is_horizontal_or_vertical(theta, tolerance_degrees=10):
    horizontal = np.pi / 2
    tolerance_radians = np.deg2rad(tolerance_degrees)

    return (abs(theta) < tolerance_radians or
            abs(theta - horizontal) < tolerance_radians or
            abs(theta - np.pi) < tolerance_radians)


def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def recursive_group_circles(circles, circle, group, max_distance, processed):
    for i, other_circle in enumerate(circles):
        if i not in processed:
            if distance(circle[:2], other_circle[:2]) <= max_distance:
                group.append(other_circle)
                processed.add(i)
                group, processed = recursive_group_circles(circles, other_circle, group, max_distance, processed)
    return group, processed


def group_circles_based_on_distance(circles, max_distance):
    processed = set()
    groups = []

    for i, circle in enumerate(circles):
        if i not in processed:
            group, processed = recursive_group_circles(circles, circle, [circle], max_distance, processed)
            groups.append(group)

    return groups


def find_similar_groups(groups, orientation, threshold_factor):
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
    print("The board orientation is:", orientation)

    threshold_factor = 5
    paired_groups = find_similar_groups(groups, orientation, threshold_factor)
    paired_groups_image = draw_circle_groups_pairs(input_img, paired_groups)
    cv2.imshow("Circle groups", paired_groups_image)

    return detected_img


if __name__ == "__main__":
    input_img1 = cv2.imread("/Users/geri/Desktop/MSc/diploma/project/Screenshot1.png")
    print('Opened image')
    detected_img = detect_backgammon_board(input_img1)
    cv2.imshow("Detected Backgammon Board", detected_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
