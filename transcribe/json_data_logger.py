import json
import os
from utils.logger import LOG

moves_data = []  # Initialize an empty list for moves
move_id_counter = 0  # Initialize a counter for move IDs


def add_move_to_json(dice_roll, moves):
    global moves_data, move_id_counter
    import utils.globals as globals

    LOG.info(globals.last_move_time)
    move_id_counter += 1  # Increment the ID counter for each new move

    move_data = {
        "id": "move" + str(move_id_counter),  # Generate a unique ID for the move
        "timestamp": globals.last_move_time,
        "dice_roll": dice_roll,
        "not_ambiguous": globals.is_ambiguous,
        "moves": moves
    }
    moves_data.append(move_data)

    # Create the directory if it does not exist
    if not os.path.exists('./result'):
        os.makedirs('./result')

    with open('./result/moves_data.json', 'w') as file:
        json.dump(moves_data, file, indent=4)

    globals.is_ambiguous = True
