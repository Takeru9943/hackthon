import requests
import base64
import json
import pprint
import cv2

# 動画ファイルのパスを指定する
video_path = "/Users/fumi/PycharmProjects/pythonProject/multimodal/a2g1n-20lik.mp4"  # 自分の動画ファイルのパスに変更してください
cap = cv2.VideoCapture(video_path)

# 表情認識用のAPI情報を設定する
endpoint = 'https://api-us.faceplusplus.com'
api_key = "SK7WRvwNYjP5cVHQqzKNcUEU1J7PzxX3"  # ご自身の「API Key」を入力する
api_secret = "9ZLk4Teaxa0l1USu-EuCfJ_Sgv6YbdyN"  # ご自身の「API Secret」を入力する

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

# 最大値と最小値を表示する
print("Max Happiness:", max_happiness, "t =", t_max_happiness)
print("Min Happiness:", min_happiness, "t =", t_min_happiness)
print("Max Neutral:", max_neutral, "t =", t_max_neutral)
print("Min Neutral:", min_neutral, "t =", t_min_neutral)
print("Max Sadness:", max_sadness, "t =", t_max_sadness)
print("Min Sadness:", min_sadness, "t =", t_min_sadness)
