from flask import Flask, render_template, request, redirect, url_for, jsonify
import openai
import os
import requests
import base64
import pprint
import cv2
import subprocess
from pydub import AudioSegment
from google.cloud import speech
import json

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'secret.json'

app = Flask(__name__)
# 表情認識用のAPI情報を設定する
endpoint = 'https://api-us.faceplusplus.com'
api_key = "my_api_key"  # ご自身の「API Key」を入力する
api_secret = "my_api_secret"  # ご自身の「API Secret」を入力する


# アップロードされた動画を保存するディレクトリのパス
UPLOAD_FOLDER = './uploaded_videos'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# フレームを保存するディレクトリのパス
FRAMES_FOLDER = './static/frames'
if not os.path.exists(FRAMES_FOLDER):
    os.makedirs(FRAMES_FOLDER)

def clear_frames_folder():
    # framesディレクトリ内の.jpgファイルを全て削除する
    for file_name in os.listdir(FRAMES_FOLDER):
        if file_name.endswith(".jpg"):
            file_path = os.path.join(FRAMES_FOLDER, file_name)
            os.remove(file_path)



if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

WAV_FOLDER = './wav'
if not os.path.exists(WAV_FOLDER):
    os.makedirs(WAV_FOLDER)

CHUNK_FOLDER = './chunks'
if not os.path.exists(CHUNK_FOLDER):
    os.makedirs(CHUNK_FOLDER)

TEMP_WAV_FILE = 'temp.wav'  # 一時的なWAVファイル名

def convert_mp4_to_mono_wav(mp4_file_path, wav_file_path):
    command = f'ffmpeg -y -i {mp4_file_path} -vn -ac 1 -ar 44100 -f wav {wav_file_path}'
    subprocess.call(command, shell=True)

def convert_stereo_to_mono_wav(stereo_wav_file_path, mono_wav_file_path):
    audio = AudioSegment.from_file(stereo_wav_file_path)
    audio = audio.set_channels(1)  # モノラル変換
    audio.export(mono_wav_file_path, format="wav")

def split_wav_to_chunks(wav_file_path, chunk_length_ms=50000):
    audio = AudioSegment.from_file(wav_file_path)
    chunks = [audio[i:i+chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
    for i, chunk in enumerate(chunks):
        chunk.export(os.path.join(CHUNK_FOLDER, f"chunk{i}.wav"), format="wav")

def transcribe_file(content, lang='日本語'):
    lang_code = {
        '英語': 'en-US',
        '日本語': 'ja-JP',
    }
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code=lang_code[lang]
    )
    response = client.recognize(config=config, audio=audio)
    return response

def get_valid_files(directory):
    valid_files = []
    for file_name in os.listdir(directory):
        if not file_name.startswith('.DS_Store'):
            valid_files.append(file_name)
    return valid_files

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
    max_sadness = request.args.get('max_sadness')
    t_max_sadness = request.args.get('t_max_sadness')

    # 以下を追加：t_max_happinessとt_min_happinessに格納された文字列をフレームフォルダで探す
    max_happiness_image_path = find_image_path(t_max_happiness)
    max_sadness_image_path = find_image_path(t_max_sadness)

    # result.htmlに解析結果を表示する
    return render_template('result.html',
                        max_happiness=max_happiness,
                        t_max_happiness=t_max_happiness,
                        max_happiness_image_path=max_happiness_image_path,
                        max_sadness=max_sadness,
                        t_max_sadness=t_max_sadness,
                        max_sadness_image_path=max_sadness_image_path)

def find_image_path(target_text):
    frames_folder = '/Users/takaokayuu/Downloads/hackthon-main/static/frames'
    for filename in os.listdir(frames_folder):
        if target_text in filename:
            return url_for('static', filename=f'frames/{filename}')


@app.route('/show_frames', methods=['GET'])
def show_frames():
    # 保存されたフレームを取得する
    frame_files = os.listdir(FRAMES_FOLDER)
    frame_files.sort()

    return render_template('show_frames.html', frame_files=frame_files)

@app.route('/convert', methods=['POST'])
def convert():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        mp4_file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
        uploaded_file.save(mp4_file_path)
        wav_file_path = os.path.join(WAV_FOLDER, os.path.splitext(uploaded_file.filename)[0] + '.wav')
        convert_mp4_to_mono_wav(mp4_file_path, wav_file_path)

        # 一時的なWAVファイルを作成する
        temp_wav_file_path = os.path.join(WAV_FOLDER, TEMP_WAV_FILE)
        convert_mp4_to_mono_wav(mp4_file_path, temp_wav_file_path)

        return 'MP4 file has been converted to WAV successfully!', 200
    return 'No file has been uploaded!', 400

@app.route('/split', methods=['POST'])
def split():
    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        wav_file_path = os.path.join(WAV_FOLDER, uploaded_file.filename)
        uploaded_file.save(wav_file_path)

        # モノラルに変換したWAVファイルを作成する
        mono_wav_file_path = os.path.join(WAV_FOLDER, 'mono_' + os.path.splitext(uploaded_file.filename)[0] + '.wav')
        convert_stereo_to_mono_wav(wav_file_path, mono_wav_file_path)

        split_wav_to_chunks(mono_wav_file_path)
        return 'WAV file has been split into chunks successfully!', 200
    return 'No file has been uploaded!', 400

@app.route('/transcribe', methods=['POST'])
def transcribe():
    # Set the OpenAI API key
    openai.api_key = "my_open_ai_key"

    lang = request.form.get('lang')
    original_transcripts = []
    for i, wav_file in enumerate(sorted(get_valid_files(CHUNK_FOLDER), key=lambda x: int(x[5:-4]))):
        with open(os.path.join(CHUNK_FOLDER, wav_file), "rb") as f:
            content = f.read()
        response = transcribe_file(content, lang=lang)
        for result in response.results:
            original_transcript = result.alternatives[0].transcript
            original_transcripts.append(original_transcript)

    # Prepare the prompt for the ChatGPT API
    original_text = " ".join(original_transcripts)

    # Call the ChatGPT API
    chat_response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": original_text},
            {"role": "assistant", "content": "面接にふさわしい言葉遣いや言い回しに変更し面接官の印象が良くなるようにしてください,文字数はあまり増やさないで"},
        ],
        temperature=0.8,
    )

    # Extract the improved text from the response
    improved_transcript = chat_response['choices'][0]['message']['content'].strip()

    # Redirect to result2.html with the transcripts
    return render_template('result2.html', original=original_text, improved=improved_transcript)






if __name__ =='__main__':
    app.run(debug=True)
