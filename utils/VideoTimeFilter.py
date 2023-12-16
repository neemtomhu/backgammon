import logging

import cv2


class VideoTimeFilter(logging.Filter):
    def __init__(self, cap):
        super().__init__()
        self.cap = cap

    def filter(self, record):
        current_time_msec = self.cap.get(cv2.CAP_PROP_POS_MSEC)
        current_time_str = "{:02d}:{:02d}:{:02d}".format(int(current_time_msec // 3600000),
                                                         int((current_time_msec % 3600000) // 60000),
                                                         int((current_time_msec % 60000) // 1000))
        record.video_time = current_time_str
        return True
