import cv2
from deepface import DeepFace

# カメラを開く
cap = cv2.VideoCapture(0)

while True:
    # カメラから画像を取得
    ret, frame = cap.read()

    # 顔の検出
    faces = DeepFace.detectFace(frame)

    for face in faces:
        # 顔の座標
        x, y, w, h = face['box']

        # 顔の部分を切り取る
        face_roi = frame[y:y + h, x:x + w]

        # 顔の感情を推定する
        result = DeepFace.analyze(face_roi, actions=['emotion'])

        # 推定された感情を取得
        emotion = result['dominant_emotion']

        # 顔の周囲に枠と感情を表示する
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        cv2.putText(frame, emotion, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    # 画像を表示する
    cv2.imshow('Emotion Detection', frame)

    # 'q'キーを押して終了
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# カメラをリリースし、ウィンドウを閉じる
cap.release()
cv2.destroyAllWindows()
