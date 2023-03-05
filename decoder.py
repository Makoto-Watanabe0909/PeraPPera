#============================
#【定義】
import Database
import global_value as g
from camera import Camera
from flask import Flask, request,render_template, Response
import cv2
import os
import numpy as np
import shutil
import simpleaudio
import soundfile as sf
from PIL import Image, ImageFile
#from tty import CFLAG

#============================
#【セットアップ】
app = Flask(__name__)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True
ImageFile.LOAD_TRUNCATED_IMAGES = True

#ドットの配列のタテヨコ
g.dotsColumns = 100
g.dotsRows = 640

#============================
@app.route('/', methods=['GET', 'POST'])
def main():
    Camera().__init__()

    return render_template('form_decode.html', message_path="../static/messages/100600.png")

#============================
#【カメラ映像】
def gen(camera):
    while True:
        g.frame = camera.get_frame()
        if g.frame is not None:
            yield (b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + g.frame.tobytes() + b"\r\n")
        else:
            print("***PeraPPera : camera is none")

@app.route("/video_feed")
def video_feed():
    return Response(gen(Camera()),
            mimetype="multipart/x-mixed-replace; boundary=frame")

#============================
#【入力部分】
@app.route('/toSet', methods=['GET', 'POST'])
def form():

    messageToSizeChoice = "default"

    if request.method == 'POST':
        answer = request.form.get('type')

        if answer == "typeA":
            g.dotsColumns = 250
            g.dotsRows = 250
            messageToSizeChoice = "250250"
        elif answer == "typeB":
            g.dotsColumns = 200
            g.dotsRows = 320
            messageToSizeChoice = "200320"
        elif answer == "typeC":
            g.dotsColumns = 100
            g.dotsRows = 640
            messageToSizeChoice = "100600"

        print("***PeraPPera : Resolution : " + str(g.dotsColumns) + "×" + str(g.dotsRows))

    if os.path.isfile("static/images/projection.png"):
        return render_template('form_decode.html', image_path="static/images/projection.png", message_path="../static/messages/" + messageToSizeChoice + ".png")
    else:
        return render_template('form_decode.html', message_path="../static/messages/" + messageToSizeChoice + ".png")

@app.route("/reloadProjection", methods=["POST"])
def reloadProjection():
    print("***PeraPPera : reload")

    if os.path.isfile("image/messages/default.png"):
        print("existence")
    else:
        print("no exist")

    if os.path.isfile("static/images/projection.png"):
        return render_template('form_decode.html', message_path="../static/messages/default.png", image_path="static/images/projection.png")
    else:
        return render_template('form_decode.html', message_path="../static/messages/default.png")

#============================
#【デコード】
@app.route("/toDecode", methods=["POST"])
def toDecode():
    print("decode!")

    #2つの器を用意
    buffer = []
    if os.path.isfile("static/images/projection.png"):
        im = cv2.imread("static/images/projection.png")
    else:
        print("***PeraPPera : no projection image")
        return render_template('form_decode.html', message_path="../static/messages/nodatatodecode.png")

    for i in range(g.dotsRows-1): #端っこは白が混ざっていて読み取りたくないので読み取る行を減らしている。
        #convertVar.set(int((i/(g.dotsRows-1))*100))#進捗バーの更新

        for j in range(g.dotsColumns-1): #端っこは白が混ざっていて読み取りたくないので読み取る列を減らしている。
            pX = int(j+2)#端っこは白が混ざっていて読み取りたくないので読み取る列を減らしている。
            pY = int(i+2)

            rawcolor = im[pY,pX]  #色の取得

            for k in range(3):#音波に直してバッファに追加
                buffer.append(eval("Database.ThreeToOneCS(rawcolor[" + str(k) + "])"))

            print("processed pix : ", pX, "," , pY)
            print("color : ", rawcolor)
            print("==========================")

    #溜まったデータをwavに変換
    sr = 48000
    filepath = "static/sound/decoded.wav"
    _format = "WAV"
    subtype = 'PCM_24'
    sf.write(filepath,  buffer, sr, format=_format, subtype=subtype)

    print("***PeraPPera : soundfile generated!")

    if os.path.isfile("static/images/projection.png"):
        return render_template('form_decode.html', image_path="static/images/projection.png", message_path="../static/messages/youraudioisready.png")
    else:
        return render_template('form_decode.html', message_path="../static/messages/youraudioisready.png")

#============================
#【再生】

@app.route("/toPlay", methods=["POST"])
def toPlay():
    print("***PeraPPera : play!")

    filepath = "static/sound/decoded.wav"

    if os.path.isfile(filepath):
        wav_obj = simpleaudio.WaveObject.from_wave_file(filepath)
        play_obj = wav_obj.play()
        play_obj.wait_done()  #再生終わるまで待機
        print("***PeraPPera : play_finished")
    else:
        print("***PeraPPera : no decoded audio data")

        if os.path.isfile("static/images/projection.png"):
            return render_template('form_decode.html', image_path="static/images/projection.png", message_path="../static/messages/default.png")
        else:
            return render_template('form_decode.html', message_path="../static/messages/default.png")

    if os.path.isfile("static/images/projection.png"):
        return render_template('form_decode.html', image_path="static/images/projection.png", message_path="../static/messages/youraudioisready.png")
    else:
        return render_template('form_decode.html', message_path="../static/messages/youraudioisready.png")

#============================
#【抹消】

@app.route("/toDelete", methods=["POST"])
def toDelete():

    if os.path.isfile("static/sound/decoded.wav"):
        os.remove("static/sound/decoded.wav")
        print("***PeraPPera : deleted")
    else:
        print("***PeraPPera : file to delete not found")

    #画像が入ってるディレクトリごと消去→作成
    shutil.rmtree("static/images")
    os.mkdir("static/images")

    return render_template('form_decode.html', message_path="../static/messages/yourdatahasbeendeleted.png")

#============================
#【システム関連】
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.get('/shutdown')
def shutdown():
    shutdown_server()
    return 'Server shutting down...'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=18920, debug=True, threaded=True)
