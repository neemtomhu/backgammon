import logging

from utils.VideoTimeFilter import VideoTimeFilter

LOG = logging.getLogger()


def init_logging(cap):
    logging.basicConfig(
        # format='%(video_time)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
        format='%(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
        level=logging.INFO)

    # Add the filter to the root logger
    # LOG.addFilter(VideoTimeFilter(cap))

    return LOG
