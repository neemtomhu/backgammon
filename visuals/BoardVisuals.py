import math

import numpy as np

from utils.logger import LOG
from visuals.Observable import Observable


class BackgammonBoardVisuals(Observable):
    _instance = None

    corners = None  # top_left, top_right, bottom_left, bottom_right
    fields = None
    orientation = None
    checker_diameter = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            LOG.debug('Initializing board visuals')
            cls._instance = super(BackgammonBoardVisuals, cls).__new__(cls)
        return cls._instance

    def get_field_by_id(self, field_id):
        return self.fields[field_id]

    def get_nearest_field_id(self, x, y):
        LOG.debug(f'Calculating nearest field to x={x}, y={y}')
        min_distance = float('inf')
        nearest_field_id = None

        for field_id, field in enumerate(self.fields):
            if field is not None:
                # Calculate the center of the field
                cx = (field.endpoints[0] + field.endpoints[2]) / 2
                cy = (field.endpoints[1] + field.endpoints[3]) / 2

                # Calculate the distance from the center to the given x, y
                distance = math.sqrt((cx - x) ** 2 + (cy - y) ** 2)

                # Update the nearest field id
                if distance < min_distance:
                    min_distance = distance
                    nearest_field_id = field_id

        return nearest_field_id

    @staticmethod
    def initialize(corners, orientation):
        BackgammonBoardVisuals.corners = corners
        BackgammonBoardVisuals.fields = [None] * 26
        BackgammonBoardVisuals.orientation = orientation

    def set_starting_fields_from_checker_groups(self, ordered_paired_groups):
        # Calculate bar position
        self.fields[0] = Field([self.corners[0][0],
                               ((self.corners[0][1] + self.corners[2][1]) / 2),
                               self.corners[1][0],
                               ((self.corners[1][1] + self.corners[3][1]) / 2)], 0, 0)

        # Calculate bar position
        bar_x = (self.corners[0][0] + self.corners[3][0]) / 2
        bar_y = (self.corners[0][1] + self.corners[2][1]) / 2
        self.fields[0] = Field([bar_x, bar_y, bar_x, bar_y], 0, 0)

        # Calculate field 1 and 24
        field_1_x1, field_1_y1, field_1_x2, field_1_y2, field_24_x1, field_24_y1, field_24_x2, field_24_y2 = \
            self.get_field_endpoints_from_group(ordered_paired_groups[0])
        self.fields[1] = Field([field_1_x1, field_1_y1, field_1_x2, field_1_y2], 1, len(ordered_paired_groups[0][0]))
        self.fields[24] = Field([field_24_x1, field_24_y1, field_24_x2, field_24_y2], 24, len(ordered_paired_groups[0][1]))

        # Calculate field 6 and 19
        field_6_x1, field_6_y1, field_6_x2, field_6_y2, field_19_x1, field_19_y1, field_19_x2, field_19_y2 = \
            self.get_field_endpoints_from_group(ordered_paired_groups[1])
        self.fields[6] = Field([field_6_x1, field_6_y1, field_6_x2, field_6_y2], 6, 5)
        self.fields[19] = Field([field_19_x1, field_19_y1, field_19_x2, field_19_y2], 19, 5)

        # Calculate field 8 and 17
        field_8_x1, field_8_y1, field_8_x2, field_8_y2, field_17_x1, field_17_y1, field_17_x2, field_17_y2 = \
            self.get_field_endpoints_from_group(ordered_paired_groups[2])
        self.fields[8] = Field([field_8_x1, field_8_y1, field_8_x2, field_8_y2], 8, 3)
        self.fields[17] = Field([field_17_x1, field_17_y1, field_17_x2, field_17_y2], 17, 3)

        # Calculate field 12 and 13
        field_12_x1, field_12_y1, field_12_x2, field_12_y2, field_13_x1, field_13_y1, field_13_x2, field_13_y2 = \
            self.get_field_endpoints_from_group(ordered_paired_groups[3])
        self.fields[12] = Field([field_12_x1, field_12_y1, field_12_x2, field_12_y2], 12, 5)
        self.fields[13] = Field([field_13_x1, field_13_y1, field_13_x2, field_13_y2], 13, 5)

        # Calculate remaining fields
        ranges_and_params = [
            (range(2, 6), 1, 6, 5, 1),
            (range(7, 12), 8, 12, 4, 8),
            (range(14, 19), 13, 17, 4, 17),
            (range(20, 24), 19, 24, 5, 19)
        ]

        for r, start, end, distance, offset in ranges_and_params:
            for i in r:
                if not (i == 8 or i == 17):
                    LOG.debug(f'Calculating field: {i}')
                    self.fields[i] = self.calculate_field(start, end, distance, i, offset)
                    LOG.debug(f'Field[{i}]: {self.fields[i].endpoints}')

    def get_field_endpoints_from_group(self, checker_group_pair):
        group1 = checker_group_pair[0]
        group2 = checker_group_pair[1]
        if self.orientation == 'vertical':
            field_1_x1 = self.corners[0][0]
            field_1_y1 = group1[0][:2][1]
            field_1_x2 = (self.corners[0][0] + self.corners[3][0]) / 2
            field_1_y2 = (field_1_y1 + group2[-1][:2][1]) / 2
            field_2_x1 = self.corners[1][0]
            field_2_y1 = group2[-1][:2][1]
            field_2_x2 = field_1_x2
            field_2_y2 = field_1_y2

        return field_1_x1, field_1_y1, field_1_x2, field_1_y2, field_2_x1, field_2_y1, field_2_x2, field_2_y2

    def calculate_field(self, base_field_start, base_field_end, total_distance, field_number, offset):
        y1_distance = (self.fields[base_field_end].endpoints[1] - self.fields[base_field_start].endpoints[1]) / total_distance
        y2_distance = (self.fields[base_field_end].endpoints[3] - self.fields[base_field_start].endpoints[3]) / total_distance
        x1 = self.corners[0][0] if field_number <= 12 else self.corners[1][0]
        y1 = self.fields[offset].endpoints[1] + (field_number - offset) * y1_distance
        x2 = self.fields[offset].endpoints[2]
        y2 = self.fields[offset].endpoints[3] + (field_number - offset) * y2_distance
        field = Field([x1, y1, x2, y2], field_number, 0)
        LOG.debug(f'Field [{field.field_number}], checkers={field.checkers}')
        return field


class Field:
    def __init__(self, endpoints, field_number, checkers):
        self.endpoints = [int(endpoint) for endpoint in endpoints]  # tuple representing the center line of the field
        self.field_number = field_number  # integer between 1 and 24
        self.checkers = checkers


class Checker:  # TODO this may be removed
    def __init__(self, center, color, field_number):
        self.center = center  # tuple representing the center of the checker
        self.color = color  # string representing the color of the checker
        self.field_number = field_number  # integer between 1 and 24
