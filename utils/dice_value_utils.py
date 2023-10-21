import itertools

from utils.logger import LOG


def possible_dice_values_from_move(moved_from, moved_to):
    LOG.info(f'Deducing possible dice values from move: moved_from={moved_from}, moved_to={moved_to}')

    # Calculate absolute distances
    distances = [abs(to_ - from_) for from_, to_ in zip(moved_from, moved_to)]

    # Handle double dice values
    possible_values = set()
    if len(set(distances)) == 1:  # All distances are the same
        d = int(distances[0] / 2)
        if d <= 12:  # Check if double the distance is a valid dice roll
            possible_values.add((d, d))
            return possible_values

    # Filter distances to be in the range 1-6
    distances = [d for d in distances if 1 <= d <= 6]

    # Get permutations of distances
    possible_values.update(itertools.permutations(distances, 2))

    # Add the sum of distances if it's in the range 1-6
    total_distance = sum(distances)
    if 1 <= total_distance <= 6:
        possible_values.add((total_distance,))

    return possible_values


def is_move_possible(start, end, dice_value, board_state):
    # TODO this needs to check board state
    LOG.info(f'Validating if move is possible: start={start}, end={end}, dice_value={dice_value}')
    distance = abs(start - end)
    if (distance % dice_value) != 0 and distance > (dice_value * 4):
        LOG.info('False: distance does not match dice value')
        return False
    # Check if there is more than one opponent on the end field
    if (board_state[start] * board_state[end]) < 0 and abs(board_state[end]) > 1:
        LOG.info('More than one opponent on end field')
        return False
    return True


def deduce_dice(detected_dice, moved_from, moved_to, board_state, turn):
    LOG.info(
        f'Deducing possible dice values detected_dice={detected_dice}, moved_from={moved_from}, moved_to={moved_to}')
    # If dice values are detected and match the moves, return them
    total_movement = abs(sum(moved_from) - sum(moved_to))
    if sum(detected_dice) == total_movement:
        LOG.info(f'{sum(detected_dice)} == {total_movement}')
        if all(is_move_possible(f, t, d, board_state) for f, t, d in zip(moved_from, moved_to, detected_dice)):
            return detected_dice, moved_from, moved_to

    # If any of the moved_to is the opponents checker, then the checker has been hit
    if any(board_state[x] * turn < 0 for x in moved_from):
        for idx, x in enumerate(moved_from):
            if board_state[x] * turn < 0:
                if x not in moved_to:
                    moved_to.append(x)

    # In case a checker was hit, remove the move to field 0
    moved_to = [x for x in moved_to if x != 0]

    # If player -1 moves checker from the bar set it as field 25
    if turn == -1:
        moved_from = [25 if x == 0 else x for x in moved_from]

    # If only one move is detected, but doesn't match dice values
    if len(moved_from) == 1 and total_movement != sum(detected_dice):
        if 6 < total_movement <= 12:
            # Deduce the possible dice values that add up to the total movement
            possible_dice_combinations = [(i, total_movement - i) for i in range(1, 7) if 1 <= total_movement - i <= 6]
            for dice_combination in possible_dice_combinations:
                moves = [(moved_from[0], moved_from[0] + dice_combination[0], dice_combination[0]),
                         (moved_from[0] + dice_combination[0], moved_to[0], dice_combination[1])]

                if dice_combination[0] != dice_combination[1] and all(
                        is_move_possible(f, t, d, board_state) for f, t, d in
                        moves):
                    return list(dice_combination), moved_from, moved_to
        # TODO handle sub 6 sums
        else:
            return [], moved_from, moved_to

    # If only one move is detected, but two dice values are present
    if len(moved_from) == 1 and 4 < total_movement <= 24:
        LOG.info(f'{len(moved_from)} == 1')
        if is_move_possible(moved_from[0], moved_to[0], sum(detected_dice), board_state):
            return list(detected_dice), moved_from, moved_to

    # If two moves are detected, but they don't match the detected dice
    if len(moved_from) == 2:
        possible_values = possible_dice_values_from_move(moved_from, moved_to)
        LOG.info(f'Possible dice values: {possible_values}')
        for dice_combination in possible_values:
            if all(is_move_possible(f, t, d, board_state) for f, t, d in zip(moved_from, moved_to, dice_combination)):
                return list(dice_combination), moved_from, moved_to

    # If no dice values are detected, deduce from the moves
    if not detected_dice:
        possible_values = possible_dice_values_from_move(moved_from, moved_to)
        for dice_combination in possible_values:
            if all(is_move_possible(f, t, d, board_state) for f, t, d in zip(moved_from, moved_to, dice_combination)):
                return list(dice_combination), moved_from, moved_to

    # If nothing matches, return an error or a default value
    return [], moved_from, moved_to
