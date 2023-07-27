# app.py

from flask import Flask, render_template
from flask_socketio import SocketIO
import random
import threading
import time
import plotly
import plotly.graph_objects as go
import json

app = Flask(__name__)
socketio = SocketIO(app)

def generate_emotion_data():
    # 仮の感情データを生成してWebSocketを介してクライアントに送信する
    while True:
        emotions = ["喜び", "怒り", "驚き", "悲しみ"]
        emotion_percentages = [random.random(), random.random(), random.random(), random.random()]

        # WebSocketでデータを送信
        socketio.emit('update_emotion', {'emotions': emotions, 'emotion_percentages': emotion_percentages}, namespace='/')

        # グラフを作成し、JSON形式に変換してWebSocketで送信
        fig = go.Figure(data=[go.Bar(x=emotions, y=emotion_percentages)])
        graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        socketio.emit('update_graph', graph_json, namespace='/')

        time.sleep(1)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # WebSocket通信を開始
    threading.Thread(target=generate_emotion_data).start()
    socketio.run(app, debug=True)