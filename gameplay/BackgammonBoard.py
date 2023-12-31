from utils.logger import LOG

WHITE_BAR = 0
BLACK_BAR = 25
WHITE_PLAYER = 1
BLACK_PLAYER = -1


class BackgammonBoard:
    def __init__(self):
        self.board = [
            0,  # Bar position for non-white player
            2, 0, 0, 0, 0, -5, 0, -3, 0, 0, 0, 5,  # Positions 1-12
            -5, 0, 0, 0, 3, 0, 5, 0, 0, 0, 0, -2,  # Positions 13-24
            0  # Bar position for white player
        ]

    def has_checkers_on_bar(self, player):
        bar_position = WHITE_BAR if player == WHITE_PLAYER else BLACK_BAR
        LOG.debug(f'Player {player} has checkers on bar: {self.board[bar_position] > 0}')
        return self.board[bar_position] > 0

    def point_is_blocked(self, point, player):
        return self.board[point] * player < -1

    def checker_on_point_can_be_hit(self, point, player):
        return self.board[point] * player == -1

    def can_bear_off(self, player):
        home_board_points = range(1, 7) if player == -1 else range(19, 25)
        return all(self.board[i]*player >= 0 for i in home_board_points)

    def checker_at_position(self, start, player):
        return self.board[start] * player > 0

    def bear_off_checker(self, start, player):
        self.board[start] -= player

    def move_checker(self, start, end, player):
        LOG.info(f'Move {start} -> {end}')
        hit_was_made = False

        if self.checker_on_point_can_be_hit(end, player):
            self.board[end] = 0
            if player < 1:
                self.board[0] += player * -1
            else:
                self.board[25] += player * -1
            hit_was_made = True
        self.board[start] -= player
        if end != 0 and end != 25:
            self.board[end] += player
        LOG.info(f'Board: {self.board}')
        return hit_was_made
