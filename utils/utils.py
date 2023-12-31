import cv2
import numpy as np

from utils.logger import LOG
from visuals import BoardVisuals


def order_checkers(paired_groups):
    ordered_groups = reorder_paired_groups(paired_groups)
    ordered_checkers = reorder_checkers_within_groups(ordered_groups)
    return order_checker_group_pairs(ordered_checkers)


def reorder_paired_groups(paired_groups):
    # Initialize index and minimum length
    min_length_index = 0
    min_length = len(paired_groups[0][0]) + len(paired_groups[0][1])

    # Loop through paired_groups to find the one with minimum total checkers
    for i in range(1, len(paired_groups)):
        total_checkers = len(paired_groups[i][0]) + len(paired_groups[i][1])
        if total_checkers < min_length:
            min_length = total_checkers
            min_length_index = i

    # Reorder the paired_groups based on their distance to the starting position group
    starting_position = get_checker_group_axis(paired_groups[min_length_index][0])
    distances = [(i, np.abs(starting_position - get_checker_group_axis(group[0]))) for i, group in
                 enumerate(paired_groups)]
    distances.sort(key=lambda x: x[1])

    reordered_indices = [index for index, _ in distances]
    reordered_paired_groups = [paired_groups[index] for index in reordered_indices]

    return reordered_paired_groups


def order_checker_group_pairs(paired_groups):
    reordered_paired_groups = []
    for pair in paired_groups:
        if pair[0][0][0] > pair[1][0][0]:
            reordered_paired_groups.append([pair[1], pair[0]])
        else:
            reordered_paired_groups.append(pair)

    return reordered_paired_groups


def reorder_checkers_within_groups(paired_groups):
    reordered_paired_groups = []

    for pair in paired_groups:
        reordered_pair = []

        for group in pair:
            # Sort checkers based on their x-coordinates (left to right)
            reordered_group = sorted(group, key=lambda checker: checker[0])

            reordered_pair.append(reordered_group)

        reordered_paired_groups.append(reordered_pair)

    return reordered_paired_groups


def draw_field(img, field):
    if field:
        LOG.debug(f'Endpoints: {field.endpoints}')
        cv2.line(img, (field.endpoints[0], field.endpoints[1]), (field.endpoints[2], field.endpoints[3]), (255, 255, 255), 1)
    return img


def draw_group_axes(img, ordered_paired_groups):
    # for pair in ordered_paired_groups:
    #     img = get_group_axis(img, pair)
    set_starting_fields_from_checker_groups(ordered_paired_groups)
    for field in BoardVisuals.BackgammonBoardVisuals.fields:
        draw_field(img, field)
    return img


def get_checker_group_axis(checker_group):
    avg_y = sum([checker[1] for checker in checker_group]) / len(checker_group)
    return avg_y


def set_starting_fields_from_checker_groups(ordered_paired_groups):
    BoardVisuals.BackgammonBoardVisuals().set_starting_fields_from_checker_groups(ordered_paired_groups)


def rotate_input_image_clockwise(image):
    rotated = cv2.transpose(image)  # This essentially swaps the rows and columns
    return cv2.flip(rotated, flipCode=1)
