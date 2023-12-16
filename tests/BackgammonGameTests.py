import unittest

from gameplay.BackgammonGame import BackgammonGame


class BackgammonGameTests(unittest.TestCase):

    def test_has_checkers_on_bar(self):
        game = BackgammonGame()
        game.board.board[0] = 1
        self.assertEqual(game.board.has_checkers_on_bar(1), True)
        game.board.board[0] = 0
        self.assertEqual(game.board.has_checkers_on_bar(1), False)

    def test_point_is_blocked(self):
        game = BackgammonGame()
        game.board.board[6] = -2
        self.assertEqual(game.board.point_is_blocked(6, 1), True)
        game.board.board[6] = 1
        self.assertEqual(game.board.point_is_blocked(6, 1), False)

    def test_can_bear_off(self):
        game = BackgammonGame()
        game.board.board = [0, -2, -2, -2, -2, -2, -2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.assertEqual(game.board.can_bear_off(-1), True)

    def test_make_move(self):
        game = BackgammonGame()
        game.set_dice([6, 1])
        self.assertEqual(game.make_move(24, 18), True)   # valid move
        self.assertEqual(game.make_move(24, 17), False)  # invalid move
        self.assertEqual(game.make_move(18, 17), False)  # invalid move
        self.assertEqual(game.make_move(24, 18), False)  # no more 6 to move
        self.assertEqual(game.make_move(8, 7), True)     # valid move
        self.assertEqual(game.make_move(8, 7), False)    # invalid move, no moves left

    def test_switch_turn(self):
        game = BackgammonGame()
        self.assertEqual(game.turn, 1)
        game.switch_turn()
        self.assertEqual(game.turn, -1)


if __name__ == '__main__':
    unittest.main()
