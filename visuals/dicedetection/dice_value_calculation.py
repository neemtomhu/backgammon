def calculate_dice_roll_from_move(removed_from, moved_to):
    # Check if the lengths of the lists are valid
    if len(removed_from) != len(moved_to) or len(removed_from) > 2 or len(moved_to) > 2:
        raise ValueError("Invalid input lists")

    # Calculate the distances for each checker movement
    distances = [abs(removed - moved) for removed, moved in zip(removed_from, moved_to)]

    # If only one checker is moved
    if len(distances) == 1:
        distance = distances[0]
        possible_rolls = {(min(i, distance - i), max(i, distance - i)) for i in range(1, 7) if 1 <= distance - i <= 6}
        return list(possible_rolls)

    # If two checkers are moved
    else:
        possible_rolls = set()
        for i in range(1, 7):
            for j in range(1, 7):
                if (i == distances[0] and j == distances[1]) or (i == distances[1] and j == distances[0]):
                    possible_rolls.add((min(i, j), max(i, j)))
        return list(possible_rolls)


def get_most_likely_dice_roll(possible_dice_rolls, removed_from, moved_to):
    # Calculate the absolute differences between the starting and ending positions
    distances = [abs(end - start) for start, end in zip(removed_from, moved_to)]

    # Count how many times each possible dice roll appears in the distances
    dice_counts = {dice: distances.count(dice) for dice in possible_dice_rolls}

    # Sort the possible dice rolls based on their counts in descending order
    sorted_dice = sorted(dice_counts.keys(), key=lambda x: dice_counts[x], reverse=True)

    # Return the two most likely dice rolls
    return sorted_dice[:2]
