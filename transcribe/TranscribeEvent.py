import logging

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
        move_events = ''
        logged_moves = []
        for move in self.moves:
            if move in logged_moves:
                continue
            if move[0] in [0, 25]:
                move[0] = 'bar'
            if move[1] in [0, 25]:
                move[1] = 'off'
            if self.moves.count(move) > 1:
                move_events += f' {move[0]}/{move[1]}({self.moves.count(move)})'
            else:
                move_events += f' {move[0]}/{move[1]}'
            logged_moves.append(move)

        if len(self.moves) == 1:
            log_message(f'{self.dice_roll_log}{move_events}.')
            add_move_to_json(self.dice_roll_log, f'{move_events}.')
        else:
            log_message(f'{self.dice_roll_log}{move_events}')
            add_move_to_json(self.dice_roll_log, f'{move_events}.')
        self.dice_roll_log = ''
        self.moves = []
