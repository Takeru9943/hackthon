from flask import Flask, render_template, request, redirect, url_for, jsonify
import requests
import base64
import json
import cv2
import os
import time

app = Flask(__name__)

# 表情認識用のAPI情報を設定する
endpoint = 'https://api-us.faceplusplus.com'
api_key = "SK7WRvwNYjP5cVHQqzKNcUEU1J7PzxX3"  # ご自身の「API Key」を入力する
api_secret = "9ZLk4Teaxa0l1USu-EuCfJ_Sgv6YbdyN"  # ご自身の「API Secret」を入力する

# アップロードされた動画を保存するディレクトリのパス
UPLOAD_FOLDER = './uploaded_videos'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# フレームを保存するディレクトリのパス
FRAMES_FOLDER = './frames'
if not os.path.exists(FRAMES_FOLDER):
    os.makedirs(FRAMES_FOLDER)

def clear_frames_folder():
    # framesディレクトリ内の.jpgファイルを全て削除する
    for file_name in os.listdir(FRAMES_FOLDER):
        if file_name.endswith(".jpg"):
            file_path = os.path.join(FRAMES_FOLDER, file_name)
            os.remove(file_path)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # アップロードされたファイルを取得
        uploaded_file = request.files['file']

        # ファイルが選択されている場合
        if uploaded_file.filename != '':
            # ファイルをアップロード先ディレクトリに保存
            uploaded_file.save(os.path.join(UPLOAD_FOLDER, uploaded_file.filename))

            # 動画ファイルのパスを指定する
            video_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)

            # analyze.htmlにリダイレクトする
            return redirect(url_for('analyze', video_path=video_path))

    # GETリクエストの場合やファイルが選択されていない場合は、ファイルアップロードフォームを表示する
    return render_template('index.html')


@app.route('/analyze', methods=['GET'])
def analyze():
    video_path = request.args.get('video_path')

    # フレームを保存するディレクトリをクリアする
    clear_frames_folder()

    # 解析処理を開始する
    # 動画の解析と結果の取得
    # 変数を初期化する
    max_happiness = 0
    min_happiness = 100  # 初期値を大きな値に設定
    max_neutral = 0
    min_neutral = 100  # 初期値を大きな値に設定
    max_sadness = 0
    min_sadness = 100  # 初期値を大きな値に設定

    # 感情の最大・最小値を取得したタイミング（t）を記録する変数
    t_max_happiness = 0
    t_min_happiness = 0
    t_max_neutral = 0
    t_min_neutral = 0
    t_max_sadness = 0
    t_min_sadness = 0

    # 0.5秒ごとに表情認識を行い、動画を全て認識するループ
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    seconds_passed = 0
    frame_counter = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 画像をAPIに送る
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_base64 = base64.b64encode(img_encoded).decode('utf-8')
        response = requests.post(
            endpoint + '/facepp/v3/detect',
            {
                'api_key': api_key,
                'api_secret': api_secret,
                'image_base64': img_base64,
                'return_attributes': 'emotion'
            }
        )

        # リクエストに対して返ってきた結果を取得する
        json_dict = json.loads(response.text)
        if 'faces' in json_dict:
            if len(json_dict['faces']) > 0:
                emotions = json_dict['faces'][0]['attributes']['emotion']

                # 最大値と最小値を保持する
                if emotions['happiness'] > max_happiness:
                    max_happiness = emotions['happiness']
                    t_max_happiness = seconds_passed + 0.5

                if emotions['happiness'] < min_happiness:
                    min_happiness = emotions['happiness']
                    t_min_happiness = seconds_passed + 0.5

                if emotions['neutral'] > max_neutral:
                    max_neutral = emotions['neutral']
                    t_max_neutral = seconds_passed + 0.5

                if emotions['neutral'] < min_neutral:
                    min_neutral = emotions['neutral']
                    t_min_neutral = seconds_passed + 0.5

                if emotions['sadness'] > max_sadness:
                    max_sadness = emotions['sadness']
                    t_max_sadness = seconds_passed + 0.5

                if emotions['sadness'] < min_sadness:
                    min_sadness = emotions['sadness']
                    t_min_sadness = seconds_passed + 0.5

        # 0.5秒待機する
        cv2.waitKey(500)

        # 経過時間を更新
        seconds_passed += 0.5

        # 0.5秒ごとの画像データを保存する
        frame_filename = f"{seconds_passed}.jpg"
        frame_path = os.path.join(FRAMES_FOLDER, frame_filename)
        cv2.imwrite(frame_path, frame)

        # 動画を全て認識したらループを抜ける
        if seconds_passed >= cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps:
            break

    # 後処理としてキャプチャをリリースする
    cap.release()
    cv2.destroyAllWindows()

    # 解析完了後にresult.htmlにリダイレクトする
    return redirect(url_for('result',
                            max_happiness=max_happiness,
                            t_max_happiness=t_max_happiness,
                            min_happiness=min_happiness,
                            t_min_happiness=t_min_happiness,
                            max_neutral=max_neutral,
                            t_max_neutral=t_max_neutral,
                            min_neutral=min_neutral,
                            t_min_neutral=t_min_neutral,
                            max_sadness=max_sadness,
                            t_max_sadness=t_max_sadness,
                            min_sadness=min_sadness,
                            t_min_sadness=t_min_sadness))

@app.route('/result', methods=['GET'])
def result():
    # 解析結果を受け取る（analyze.htmlからリダイレクトされるときに値を渡す）
    max_happiness = request.args.get('max_happiness')
    t_max_happiness = request.args.get('t_max_happiness')
    min_happiness = request.args.get('min_happiness')
    t_min_happiness = request.args.get('t_min_happiness')
    max_neutral = request.args.get('max_neutral')
    t_max_neutral = request.args.get('t_max_neutral')
    min_neutral = request.args.get('min_neutral')
    t_min_neutral = request.args.get('t_min_neutral')
    max_sadness = request.args.get('max_sadness')
    t_max_sadness = request.args.get('t_max_sadness')
    min_sadness = request.args.get('min_sadness')
    t_min_sadness = request.args.get('t_min_sadness')

    # result.htmlに解析結果を表示する
    return render_template('result.html',
                           max_happiness=max_happiness,
                           t_max_happiness=t_max_happiness,
                           min_happiness=min_happiness,
                           t_min_happiness=t_min_happiness,
                           max_neutral=max_neutral,
                           t_max_neutral=t_max_neutral,
                           min_neutral=min_neutral,
                           t_min_neutral=t_min_neutral,
                           max_sadness=max_sadness,
                           t_max_sadness=t_max_sadness,
                           min_sadness=min_sadness,
                           t_min_sadness=t_min_sadness)

@app.route('/show_frames', methods=['GET'])
def show_frames():
    # 保存されたフレームを取得する
    frame_files = os.listdir(FRAMES_FOLDER)
    frame_files.sort()

    return render_template('show_frames.html', frame_files=frame_files)

if __name__ == '__main__':
    app.run()
