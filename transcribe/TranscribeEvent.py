import logging
from collections import Counter

from transcribe.file_writer import log_message
from transcribe.json_data_logger import add_move_to_json
from utils.logger import LOG


class TranscribeEvent:
    _instance = None

    @staticmethod
    def get_instance():
        if TranscribeEvent._instance is None:
            TranscribeEvent._instance = TranscribeEvent()
        return TranscribeEvent._instance

    def __init__(self):
        self.dice_roll_log = ''
        self.moves = []

    def set_dice_roll(self, dice_roll):
        LOG.info(f'Setting dice roll to {dice_roll}')
        self.dice_roll_log = f'{dice_roll[0]}{dice_roll[1]}'

    def add_move(self, move):
        self.moves.append(move)

    def log_event(self):
        move_counter = Counter(map(tuple, self.moves))

        move_events = ''
        for move, count in move_counter.items():
            # Convert special positions to 'bar' and 'off'
            start, end = move
            if start in [0, 25]:
                start = 'bar'
            if end in [0, 25]:
                end = 'off'

            # Format the move
            move_str = f'{start}/{end}'
            if count > 1:
                move_str += f'({count})'

            move_events += f' {move_str}'

        if len(move_events.strip().split()) == 1:
            log_message(f'{self.dice_roll_log}{move_events}.')
            add_move_to_json(self.dice_roll_log, f'{move_events}.')
        else:
            log_message(f'{self.dice_roll_log}{move_events}')
            add_move_to_json(self.dice_roll_log, f'{move_events}')

        # Reset the log and moves
        self.dice_roll_log = ''
        self.moves = []
