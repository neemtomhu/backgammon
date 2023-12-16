import logging
import datetime

filename = None


def log_message(message):
    global filename
    # If filename is not set, generate a filename based on the current date and time
    if filename is None:
        now = datetime.datetime.now()
        filename = now.strftime("bg_log_%Y%m%d_%H%M%S.txt")

    with open(filename, 'a') as file:
        file.write(f"{message}\n")
