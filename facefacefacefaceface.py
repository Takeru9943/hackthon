# 必要なモジュールをインポートする
import requests
import base64
import json
import pprint
import cv2

# 動画ファイルのパスを指定する
video_path = "/Users/kurokawatakeru/Github/hackthon/test.mp4" # 自分の動画ファイルのパスに変更してください
cap = cv2.VideoCapture(video_path)

# 表情認識用のAPI情報を設定する
endpoint = 'https://api-us.faceplusplus.com'
api_key = "SK7WRvwNYjP5cVHQqzKNcUEU1J7PzxX3"  # ご自身の「API Key」を入力する
api_secret = "9ZLk4Teaxa0l1USu-EuCfJ_Sgv6YbdyN"  # ご自身の「API Secret」を入力する

# 動画のフレーム数を取得する
frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

# フレームレートを取得する
fps = int(cap.get(cv2.CAP_PROP_FPS))

# 1秒ごとに表情認識を行い、動画を全て認識するループ
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

    # リクエストに対して返ってきた結果を出力する
    json_dict = json.loads(response.text)
    if 'faces' in json_dict:
        if len(json_dict['faces']) > 0:
            pprint.pprint(json_dict['faces'][0]['attributes']['emotion'])

    # 1秒待機する
    cv2.waitKey(1000)

    # 経過時間を更新
    seconds_passed += 1

    # 動画を全て認識したらループを抜ける
    if seconds_passed >= frame_count / fps:
        break

# 後処理としてキャプチャをリリースする
cap.release()
cv2.destroyAllWindows()
