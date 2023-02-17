#============================
#【定義】
import Database
import global_value as g
from camera import Camera
from flask import Flask, request,render_template, Response
import cv2
import numpy as np
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
g.moduleChoice = ""
g.dotsColumns = 80
g.dotsRows = 400

g.frame = np.array(Image.open('image/temp.png'))

#============================
#【カメラ映像】
def gen(camera):
    while True:
        g.frame = camera.get_frame()
        if g.frame is not None:
            yield (b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + g.frame.tobytes() + b"\r\n")
        else:
            print("camera is none")

@app.route("/video_feed")
def video_feed():
    return Response(gen(Camera()),
            mimetype="multipart/x-mixed-replace; boundary=frame")

#============================
#【入力部分】
@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        print("Module Choice : " + str(request.form['modu']))
        print("Resolution : " + str(request.form['resoCol']) + "×" + str(request.form['resoRow']))
        g.moduleChoice = str(request.form['modu'])
        g.dotsColumns = int(str(request.form['resoCol']))
        g.dotsRows = int(str(request.form['resoRow']))

        return render_template('form_decode.html')
    else:
        return render_template('form_decode.html')

@app.route("/reloadProjection", methods=["POST"])
def reloadProjection():
    print("reload!")
    return render_template('form_decode.html', image_path="static/images/projection.png")

#============================
#【デコード】
@app.route("/toDecode", methods=["POST"])
def toDecode():
    print("decode!")

    #2つの器を用意
    buffer = []
    im = cv2.imread("static/images/projection.png")

    for i in range(g.dotsRows-1): #端っこは白が混ざっていて読み取りたくないので読み取る行を減らしている。
        #convertVar.set(int((i/(g.dotsRows-1))*100))#進捗バーの更新

        for j in range(g.dotsColumns-1): #端っこは白が混ざっていて読み取りたくないので読み取る列を減らしている。
            pX = int(j+2)#端っこは白が混ざっていて読み取りたくないので読み取る列を減らしている。
            pY = int(i+2)

            rawcolor = im[pY,pX]  #色の取得

            for k in range(3):#音波に直してバッファに追加
                buffer.append(eval("Database.ThreeToOneCS(rawcolor[" + str(k) + "])"))
                print(".")

            print(" processed pix : ", pX, "," , pY)
            print("color : ", rawcolor)
            print("==========================")

    #溜まったデータをwavに変換
    sr = 44100
    filepath = "static/sound/decoded.wav"
    _format = "WAV"
    subtype = 'PCM_24'
    sf.write(filepath,  buffer, sr, format=_format, subtype=subtype)

    print("soundfile generated!")
    return render_template('form_decode.html')

#============================
#【再生】

@app.route("/toPlay", methods=["POST"])
def toPlay():
    print("play!")

    filepath = "static/sound/decoded.wav"
    wav_obj = simpleaudio.WaveObject.from_wave_file(filepath)
    play_obj = wav_obj.play()
    play_obj.wait_done()  #再生終わるまで待機

    print("play_finished")
    return render_template('form_decode.html')

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
