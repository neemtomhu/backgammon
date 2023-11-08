import itertools

from utils.logger import LOG


def possible_dice_values_from_move(moved_from, moved_to):
    LOG.info(f'Deducing possible dice values from move: moved_from={moved_from}, moved_to={moved_to}')

    # Generate all possible dice combinations
    all_dice_combinations = set((i, j) for i in range(1, 7) for j in range(i, 7))

    # Calculate absolute distances
    distances = [abs(to_ - from_) for from_, to_ in zip(moved_from, moved_to)]
    LOG.info(f'Calculated distances: {distances}')

    if len(distances) == 2 and max(distances) <= 6 and distances[0] != distances[1]:
        return {tuple(sorted(distances))}

    # Start with all combinations and remove those that are not possible
    # If more than 2 checkers were moved or the distance is greater than 11, it is only possible by doubles, remove all non doubles
    if len(moved_from) > 2 or sum(distances) > 11 or (len(set(distances)) == 1 and len(distances) > 1 and 0 not in moved_to and 25 not in moved_to):
        all_dice_combinations = {combo for combo in all_dice_combinations if combo[0] == combo[1] and sum(distances) <= combo[0] * 4}
        return sorted(list(all_dice_combinations), key=sort_dice_combinations_by_value)

    # for distance in distances:
    all_dice_combinations = {combo for combo in all_dice_combinations if sum(combo) >= sum(distances)}

    # If a double move was made, keep only the combinations that include the double
    if len(set(distances)) == 1 and len(distances) > 1:
        d = distances[0]
        all_dice_combinations = {combo for combo in all_dice_combinations if d in combo}

    # If a single move was made, keep combinations that sum up to the move distance
    if len(distances) == 1:
        distance = distances[0]
        all_dice_combinations = {combo for combo in all_dice_combinations if sum(combo) == distance}

    # If a move was made to bear off, adjust the combinations accordingly
    if set(moved_to) in [{0}, {25}]:
        all_dice_combinations = {combo for combo in all_dice_combinations if
                                 any(d <= distance for d in combo for distance in distances)}

    LOG.info(f'Returning possible values: {all_dice_combinations}')
    return sorted(list(all_dice_combinations), key=sort_dice_combinations_by_value)


# def possible_dice_values_from_move(moved_from, moved_to):
#     LOG.info(f'Deducing possible dice values from move: moved_from={moved_from}, moved_to={moved_to}')
#
#     all_dice_combinations = [(i, j) for i in range(1, 7) for j in range(i, 7)]
#
#     moved_from.sort()
#     moved_to.sort()
#
#     # Calculate absolute distances
#     distances = [abs(to_ - from_) for from_, to_ in zip(moved_from, moved_to)]
#     LOG.info(f'Calculated distances: {distances}')
#
#     possible_values = set()
#
#     # Handle the case when only one move was made
#     if len(distances) == 1:
#         distance = distances[0]
#         # Find two dice values that sum up to the distance
#         for i in range(1, 7):
#             for j in range(i, 7):  # Ensure we don't have duplicate pairs like (2,1) and (1,2)
#                 if i + j == distance:
#                     possible_values.add((i, j))
#         if possible_values:
#             return min(possible_values, key=sum)
#
#     # Check if the distances match any of the possible dice combinations
#     if set(distances).issubset({1, 2, 3, 4, 5, 6}):
#         if len(distances) == 2 and distances[0] != distances[1]:
#             LOG.info(f'Returning sorted distances: {tuple(sorted(distances))}')
#             return {tuple(sorted(distances))}
#
#     # Handle the case when all distances are the same and more than 2 moves were made
#     if len(set(distances)) == 1 and len(distances) > 2:
#         d = distances[0]
#         if d <= 6:
#             LOG.info(f'Returning double dice roll for more than 2 moves: {d}')
#             return {(d, d)}
#
#     # Handle double dice values
#     if len(set(distances)) == 1:
#         d = int(distances[0] / 2)
#         if d <= 6 and d >= 1:  # Check if double the distance is a valid dice roll
#             LOG.info(f'Returning double dice roll: {d}')
#             return {(d, d)}
#
#     # Handle the case when a double was rolled and the player used the dice value multiple times
#     for d in range(1, 7):
#         if all(distance in [d, 2 * d, 3 * d, 4 * d] for distance in distances) and sum(distances) <= d * 4:
#             return {(d, d)}
#         if set(moved_to) in [{0}, {25}] and any(d <= distance for distance in distances) and sum(distances) <= d * 4:
#             return {(d, d)}
#         # TODO add a check if a d, d+1 would suffice
#
#     # Filter distances to be in the range 1-6
#     distances = [d for d in distances if 1 <= d <= 6]
#
#     # Get permutations of distances
#     possible_values = set(itertools.permutations(distances, 2))
#
#     # Ensure only tuples with two elements are in the set
#     possible_values = {val for val in possible_values if len(val) == 2}
#
#     LOG.info(f'Returning possible values: {possible_values}')
#     return possible_values


def is_move_possible(start, end, dice_value, board_state):
    if start == end:
        return False

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


def can_bear_off(board_state, moved_from, turn):
    if turn == -1:
        home_board_points = range(1, 7)
        outside_home = range(7, 25)
    else:
        home_board_points = range(19, 25)
        outside_home = range(1, 19)

    # Check if all points in the home board are occupied by the player's checkers or are empty
    in_home = all(board_state[i] * turn >= 0 for i in home_board_points)

    # Check if there are no checkers outside the home board
    no_outside_checkers = all(board_state[i] * turn <= 0 for i in outside_home if i not in moved_from)

    return in_home and no_outside_checkers


def sort_dice_combinations_by_value(dice_pair):
    return sum(dice_pair) * 2 if dice_pair[0] == dice_pair[1] else sum(dice_pair)


def deduce_dice(detected_dice, moved_from, moved_to, board_state, turn):
    LOG.info(
        f'Deducing possible dice values detected_dice={detected_dice}, moved_from={moved_from}, moved_to={moved_to}')
    # If player -1 moves checker from the bar set it as field 25
    if turn == -1:
        moved_from = [25 if x == 0 else x for x in moved_from]

    # If dice values are detected and match the moves, return them
    total_movement = abs(sum(moved_from) - sum(moved_to))
    if sum(detected_dice) == total_movement and 0 not in detected_dice:
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

    # Player can bear off and moved to is missing
    if can_bear_off(board_state, moved_from, turn) and len(moved_from) > len(moved_to):
        while len(moved_from) != len(moved_to):
            moved_to.append(25 if turn == 1 else 0)

    # If player -1 moves checker from the bar set it as field 25
    if turn == -1:
        moved_from = [25 if x == 0 else x for x in moved_from]

    # If only one move is detected, but doesn't match dice values
    if len(moved_from) == 1 and total_movement != sum(detected_dice):
        if total_movement <= 12:
            # Deduce the possible dice values that add up to the total movement
            possible_dice_combinations = [(i, total_movement - i) for i in range(1, 7) if 1 <= total_movement - i <= 6]
            for dice_combination in possible_dice_combinations:
                moves = [(moved_from[0], moved_from[0] + dice_combination[0] * turn, dice_combination[0]),
                         (moved_from[0] + dice_combination[0] * turn, moved_to[0], dice_combination[1])]

                if dice_combination[0] != dice_combination[1] and all(
                        is_move_possible(f, t, d, board_state) for f, t, d in
                        moves):
                    return list(dice_combination), moved_from, moved_to
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

        # Convert to a list and sort if necessary
        sorted_possible_values = sorted(list(possible_values), key=sort_dice_combinations_by_value)

        for dice_combination in sorted_possible_values:
            if all(is_move_possible(f, t, d, board_state) for f, t, d in zip(moved_from, moved_to, dice_combination)):
                return list(dice_combination), moved_from, moved_to

    # If no dice values are detected, deduce from the moves
    # if not detected_dice:
    possible_values = possible_dice_values_from_move(moved_from, moved_to)

    # Convert to a list and sort if necessary
    sorted_possible_values = sorted(list(possible_values), key=sort_dice_combinations_by_value)

    for dice_combination in sorted_possible_values:
        if all(is_move_possible(f, t, d, board_state) for f, t, d in zip(moved_from, moved_to, dice_combination)):
            return list(dice_combination), moved_from, moved_to

    # If nothing matches, return an error or a default value
    return [], moved_from, moved_to
