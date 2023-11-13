import json
import os

from flask import Flask, render_template, jsonify, send_file

app = Flask(__name__)

# Example data storage
dynamic_texts = [
    "Initial dynamic message"
]


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/get-texts')
def get_texts():
    return jsonify(dynamic_texts)


@app.route('/add-text/<text>')
def add_text(text):
    dynamic_texts.append(text)
    return jsonify(success=True)


file_mappings = {}


@app.route('/view-video/<token>')
def view_video(token):
    file_path = file_mappings.get(token)
    if file_path and os.path.exists(file_path):
        moves_data = get_moves_data()
        return render_template('transcription_results.html', token=token, moves_data=moves_data)
    else:
        return "File not found", 404


# @app.route('/serve-video/<path:filepath>')
# def serve_video(filepath):
#     return send_file(filepath)


@app.route('/serve-video/<token>')
def serve_video(token):
    file_path = file_mappings.get(token)
    print(file_path)
    if file_path and os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "File not found", 404


def get_moves_data():
    with open('C:\\Users\\Gergely_Bodi\\PycharmProjects\\backgammon\\result\\moves_data.json', 'r') as file:
        data = json.load(file)
    return data
# def start_server():
#     app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)
