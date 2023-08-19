class BackgammonBoard:
    def __init__(self):
        self.board = [
            0,  # Bar position for non-white player
            -2, 0, 0, 0, 0, 5, 0, 3, 0, 0, 0, -5,  # Positions 1-12
            5, 0, 0, 0, -3, 0, -5, 0, 0, 0, 0, 2,  # Positions 13-24
            0  # Bar position for white player
        ]

    def has_checkers_on_bar(self, player):
        return self.board[0 if player == 1 else 25] > 0

    def point_is_blocked(self, point, player):
        return self.board[point] * player < -1

    def checker_on_point_can_be_hit(self, point, player):
        return self.board[point] * player == -1

    def can_bear_off(self, player):
        home_board_points = range(1, 7) if player == 1 else range(19, 25)
        return all(self.board[i]*player >= 0 for i in home_board_points)

    def checker_at_position(self, start, player):
        return self.board[start] * player > 0

    def bear_off_checker(self, start, player):
        self.board[start] -= player

    def move_checker(self, start, end, player):
        if self.checker_on_point_can_be_hit(end, player):
            self.board[end] = 0
            if player < 1:
                self.board[0] += player * -1
            else:
                self.board[25] += player * -1
        self.board[start] -= player
        self.board[end] += player
