from flask import Flask, render_template, request
import requests
import base64
import json
import pprint
import cv2
import os

app = Flask(__name__)

# 表情認識用のAPI情報を設定する
endpoint = 'https://api-us.faceplusplus.com'
api_key = "SK7WRvwNYjP5cVHQqzKNcUEU1J7PzxX3"  # ご自身の「API Key」を入力する
api_secret = "9ZLk4Teaxa0l1USu-EuCfJ_Sgv6YbdyN"  # ご自身の「API Secret」を入力する

# アップロードされた動画を保存するディレクトリのパス
UPLOAD_FOLDER = './uploaded_videos'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
            cap = cv2.VideoCapture(video_path)

            # 動画のフレーム数を取得する
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            # フレームレートを取得する
            fps = int(cap.get(cv2.CAP_PROP_FPS))

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
            seconds_passed = 0
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

                # 動画を全て認識したらループを抜ける
                if seconds_passed >= frame_count / fps:
                    break

            # 後処理としてキャプチャをリリースする
            cap.release()
            cv2.destroyAllWindows()

            # Webページに表示するために、最大値とその時間を返す
            return render_template('index.html', max_happiness=max_happiness, t_max_happiness=t_max_happiness)

    # GETリクエストの場合やファイルが選択されていない場合は、ファイルアップロードフォームを表示する
    return render_template('upload.html')

if __name__ == '__main__':
    app.run()
