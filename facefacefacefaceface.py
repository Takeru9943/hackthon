# ①モジュールをインポートする
import requests
import base64
import json
import pprint
import cv2
import time

# ②動画ファイルの読み込み
video_path = "/Users/fumi/PycharmProjects/pythonProject/multimodal/a2g1n-20lik.mp4"  # 読み込ませたい動画ファイルを入力する
cap = cv2.VideoCapture(video_path)

# ③フレームごとに動画を読み込み、画像として表情分析を行う
endpoint = 'https://api-us.faceplusplus.com'
api_key = "SK7WRvwNYjP5cVHQqzKNcUEU1J7PzxX3"  # ご自身の「API Key」を入力する
api_secret = "9ZLk4Teaxa0l1USu-EuCfJ_Sgv6YbdyN"  # ご自身の「API Secret」を入力する

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

    # リクエストに対して返ってきた結果を出力する
    json_dict = json.loads(response.text)
    if 'faces' in json_dict:
        if len(json_dict['faces']) > 0:
            pprint.pprint(json_dict['faces'][0]['attributes']['emotion'])

    # 0.5秒ごとに停止する（必要に応じて調整）
    time.sleep(1)

# ④後処理としてキャプチャをリリースする
cap.release()
cv2.destroyAllWindows()
