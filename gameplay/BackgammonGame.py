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

    def get_dice(self):
        return self.dice

    def make_move(self, start, end):
        LOG.info(f'Attempting move: dice={self.dice}, start={start}, end={end}')
        distance = abs(start - end)
        player = self.turn

        if not self.is_move_valid(start, end):
            LOG.info(f'Invalid move {start} -> {end}')
            return False

        self.board.move_checker(start, end, player)

        if distance in self.dice:
            self.dice.remove(distance)
        elif distance == sum(self.dice):
            self.dice = []
        else:
            # Handle the case when double was rolled
            for _ in range(int(distance / self.dice[0])):
                self.dice.remove(self.dice[0])
        LOG.info(f'Dice values: {self.dice}')

        if not self.dice:
            self.switch_turn()

        return True

    def switch_turn(self):
        self.turn *= -1  # switch player
        LOG.info(f'Switching turn to {self.turn}')

    def is_move_valid(self, start, end):
        distance = abs(start - end)
        player = self.turn
        dice = sorted(self.dice)

        if not self.board.checker_at_position(start, player):
            LOG.error(f'Player had no checker at position {start}')
            return False
        if self.board.has_checkers_on_bar(player) and start != (25 if player == -1 else 0):
            LOG.error(f'Invalid start, player {player} has checker on bar')
            return False
        if self.board.point_is_blocked(end, player):
            LOG.error(f'Point is blocked {end}')
            return False
        # if distance not in self.dice and not (self.board.can_bear_off(player) and start - player * distance <= 0):
        #     if len(dice) != 2 \
        #             or dice[0] + dice[1] != distance \
        #             or self.board.point_is_blocked(start - player * dice[0], player)\
        #             or self.board.point_is_blocked(start - player * dice[1], player):
        #         LOG.error('False')
        #         return False
        if start + player * distance <= 0 and not self.board.can_bear_off(player):
            LOG.error('False')
            return False

        return True
