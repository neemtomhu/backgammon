import json
import os

from flask import Flask, render_template, jsonify, send_file, request

app = Flask(__name__)

file_mappings = {}


@app.route('/view-video/<token>')
def view_video(token):
    file_path = file_mappings.get(token)
    if file_path and os.path.exists(file_path):
        moves_data = get_moves_data()
        return render_template('transcription_results.html', token=token, moves_data=moves_data)
    else:
        return "File not found", 404


@app.route('/serve-video/<token>')
def serve_video(token):
    file_path = file_mappings.get(token)
    print(file_path)
    if file_path and os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "File not found", 404


@app.route('/update-move', methods=['POST'])
def update_move():
    updated_move = request.json
    move_id = updated_move.get('id')

    # Check if move_id is provided
    if not move_id:
        return jsonify(success=False, message="Move ID is missing"), 400

    # Path to the moves_data.json file
    file_path = './result/moves_data.json'

    # Check if the file exists
    if not os.path.exists(file_path):
        return jsonify(success=False, message="Move data not found"), 404

    # Load existing moves
    with open(file_path, 'r') as file:
        moves_data = json.load(file)

    # Find and update the move
    for move in moves_data:
        if move.get('id') == move_id:
            move.update(updated_move)
            break
    else:
        return jsonify(success=False, message="Move not found"), 404

    # Write the updated moves back to the file
    with open(file_path, 'w') as file:
        json.dump(moves_data, file, indent=4)

    return jsonify(success=True)


def get_moves_data():
    with open('.\\result\\moves_data.json', 'r') as file:
        data = json.load(file)
    return data


if __name__ == '__main__':
    app.run(debug=True)
