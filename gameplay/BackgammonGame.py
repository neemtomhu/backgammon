from gameplay.BackgammonBoard import BackgammonBoard
from utils.logger import LOG


class BackgammonGame:
    _instance = None

    @staticmethod
    def get_instance():
        if BackgammonGame._instance is None:
            BackgammonGame._instance = BackgammonGame()
        return BackgammonGame._instance

    def __init__(self):
        self.board = BackgammonBoard()
        self.turn = 1  # white starts
        self.dice = []  # dice roll results
        self.possible_dice = []

    def set_dice(self, dice):
        self.dice = dice
        if dice[0] == dice[1]:  # doubles
            self.dice *= 2  # can be played four times

    def make_move(self, start, end):
        distance = abs(start - end)
        player = self.turn

        if not self.is_move_valid(start, end):
            LOG.info(f'Invalid move {start} -> {end}')
            return False

        self.board.move_checker(start, end, player)
        LOG.info(f'Dice values: {self.dice}')
        self.dice.remove(distance)

        if not self.dice:
            self.switch_turn()

        return True

    def switch_turn(self):
        self.turn *= -1  # switch player

    def is_move_valid(self, start, end):
        distance = abs(start - end)
        player = self.turn
        dice = sorted(self.dice)

        if not self.board.checker_at_position(start, player):
            return False
        if self.board.has_checkers_on_bar(player) and start != (25 if player == 1 else 0):
            return False
        if self.board.point_is_blocked(end, player):
            return False
        if distance not in self.dice and not (self.board.can_bear_off(player) and start - player * distance <= 0):
            if len(dice) != 2 \
                    or dice[0] + dice[1] != distance \
                    or self.board.point_is_blocked(start - player * dice[0], player)\
                    or self.board.point_is_blocked(start - player * dice[1], player):
                return False
        if start - player * distance <= 0 and not self.board.can_bear_off(player):
            return False

        return True
