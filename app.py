# app.py

from flask import Flask, render_template, request, jsonify
import os
import time
import subprocess
import multiprocessing

app = Flask(__name__)

def run_facefacefacefaceface():
    # fumifumi.pyを別プロセスとして実行
    process = subprocess.Popen(['python', 'facefacefacefaceface.py'], stdout=subprocess.PIPE, text=True)

    while True:
        # fumifumi.pyからの出力をリアルタイムに受け取る
        output = process.stdout.readline().strip()
        if output:
            app.config['emotion_data'] = output

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file uploaded'})

    file = request.files['video']
    if file.filename == '':
        return jsonify({'error': 'No video file selected'})

    if file:
        filename = os.path.join('uploads', file.filename)
        file.save(filename)
        app.config['video_filename'] = filename

        # 非同期でfumifumi.pyを実行
        multiprocessing.Process(target=run_facefacefacefaceface).start()

        return jsonify({'message': 'File uploaded successfully'})

@app.route('/analyze')
def analyze():
    return render_template('analyze.html')

@app.route('/get_emotion_data')
def get_emotion_data():
    emotion_data = app.config.get('emotion_data', '')
    return jsonify({'emotion_data': emotion_data})

if __name__ == "__main__":
    app.config['video_filename'] = ''
    app.config['emotion_data'] = ''
    app.run(debug=True)
