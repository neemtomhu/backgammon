import json


def get_moves_data(file_name):
    with open('path/to/moves_data.json', 'r') as file:
        data = json.load(file)
    return data
