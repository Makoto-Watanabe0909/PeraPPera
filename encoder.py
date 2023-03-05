#============================
#【定義】
import Database
import global_value as g
from flask import Flask, request,render_template, Response
import cv2
import os
import numpy as np
import simpleaudio
import sounddevice as sd
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
import wave
import math
import subprocess
import shutil
from io import BytesIO

#from tty import CFLAG

#============================
#【セットアップ】
app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

#ドットの配列のタテヨコ
g.dotsColumns = 100
g.dotsRows = 640
g.soundname = "no name"

g.paper = Image.open('image/temp.png')

g.chunk = 1024               # エンコード時のスプーン一杯のデータ

#============================
@app.route('/', methods=['GET', 'POST'])
def main():
    sd.default.device = 0
    return render_template('form_encode.html', message_path="../static/messages/default.png")

#============================
#【エンコード】
def toEncode():
    print("***PeraPPera : record started")

    fs = 48000
    duration = 4  # seconds
    myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
    sd.wait() #

    print("***PeraPPera : record finished")

    # ノーマライズ。量子化ビット16bitで録音するので int16 の範囲で最大化する
    myrecording = myrecording / myrecording.max() * np.iinfo(np.int16).max

    # float -> int
    myrecording = myrecording.astype(np.int16)

    filePath = "static/sound/recorded.wav"

    # ファイル保存
    with wave.open(filePath, mode='wb') as wb:
        wb.setnchannels(1)  # モノラル
        wb.setsampwidth(2)  # 16bit=2byte
        wb.setframerate(48000)
        wb.writeframes(myrecording.tobytes())  # バイト列に変換
    #===========================

    #ドットを制作===================

    #Databaseファイルから拾ってくる情報
    arucoSize = Database.arucoSize          #マーカのサイズ
    marginPaper = Database.marginPaper      #紙の上下左右の余白
    marginColor = Database.marginColor      #余白の色

    #wavファイルを読み込んでバッファに詰め込む
    data, original_samplerate = sf.read(filePath)

    #増幅用の処理
    maxData = 0
    for n in range(int(data.size)): #音声データの最大値を取得
            if (abs(data[int(n)]) > maxData):
                maxData = abs(data[int(n)])
    bairitsu = 0
    if not maxData == 0:
        bairitsu = 1/maxData #この値をかけて増幅する
    print("***PeraPPera : maxData = ", maxData, " bairitsu = ", bairitsu)

    #紙の縦幅、横幅
    width = g.dotsColumns + arucoSize*2
    height = g.dotsRows + arucoSize*2 + 2#この2はマーカとドットの間に設ける余白用

    #白紙状態（デカルト）を生成
    outputImg = np.ones((height ,width, 3), np.uint8)*255

    #音波を書き込み
    dCount = 0;  #記録したドットの数
    rgbChoice = 0
    rawColor = [0, 0, 0]
    for n in range(int(data.size)):
        if (dCount >= (g.dotsColumns * g.dotsRows)):  #範囲から溢れ出そうなものならおしまい
            break

        rawdata = data[int(n)]*bairitsu;  #-1~1
        rawColor[rgbChoice] = Database.ThreeToOneSC(rawdata)
        if rgbChoice == 0:
            rgbChoice = 1
        elif rgbChoice == 1:
            rgbChoice = 2
        elif rgbChoice == 2:
            rgbChoice = 0
            printX = arucoSize + math.floor(dCount/g.dotsColumns) + 1
            printY = arucoSize + dCount%g.dotsColumns
            outputImg[printX, printY] = np.array([rawColor[0],rawColor[1],rawColor[2]])
            dCount += 1
    #紙をpngで書き出し
    cv2.imwrite("static/images/" + g.soundname + '.png', outputImg)

    #＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝書き出した紙にマーカーを印刷＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝
    paper = Image.open("static/images/" + g.soundname + '.png')

    #マーカーの画像を読み込み→貼り付け
    for i in range(4) :
        m = Image.open('./image/marker/' + str(i) + ".png")
        pastePosX = 0 if (i%2 == 0) else (arucoSize + g.dotsColumns)#右に貼るか左に貼るか
        pastePosY = 0 if (i < 2) else (height - arucoSize + 1)
        paper.paste(m, (pastePosX, pastePosY))

    #上下左右に余白を作る https://note.nkmk.me/python-pillow-add-margin-expand-canvas/
    def add_margin(pil_img, top, right, bottom, left, color):
        widthM, heightM = pil_img.size
        new_width = widthM + right + left
        new_height = heightM + top + bottom
        result = Image.new(pil_img.mode, (new_width, new_height), color)
        result.paste(pil_img, (left, top))
        return result
    paper = add_margin(paper, marginPaper, marginPaper, marginPaper, marginPaper, (255, 255, 255))  #余白を作る（マーカの周りの余白用）
    paper = add_margin(paper, marginPaper, marginPaper, marginPaper, marginPaper, marginColor)  #余白を作る（情報印刷用）

    #リサイズする
    mag = 5  #拡大率
    (width, height) = (paper.width*mag, paper.height*mag)
    paper = paper.resize((width, height))
        
    #情報を印刷
    draw = ImageDraw.Draw(paper)
    font = ImageFont.truetype('./fonts/PixelMplus12-Regular.ttf', 28)
    outputText = "\"" + g.soundname + "\" " + str(g.dotsColumns) + "×" + str(g.dotsRows)
    draw.multiline_text((10, 5), outputText, fill=(0, 0, 0), font=font)

    #紙のサイズを整形
    if g.dotsColumns == 250:
        paper = add_margin(paper, 500, 500, 500, 500, (255, 255, 255))
    if g.dotsColumns == 200:
        paper = add_margin(paper, 400, 600, 400, 600, (255, 255, 255))
    if g.dotsColumns == 100:
        paper = add_margin(paper, 50, 0, 50, 0, (255, 255, 255))
        
    g.paper = paper
    paper.save("static/images/papertoprint.png")
    print("***PeraPPera : paper generated!!!")

#============================
#【入力部分】
@app.route('/toRecord', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        g.soundname = str(request.form['soundname'])
        answer = request.form.get('type')

        print("answer : ", answer)
        if answer == "typeA":
            g.dotsColumns = 250
            g.dotsRows = 250
        elif answer == "typeB":
            g.dotsColumns = 200
            g.dotsRows = 320
        elif answer == "typeC":
            g.dotsColumns = 100
            g.dotsRows = 640

        print("***PeraPPera : Resolution : " + str(g.dotsColumns) + "×" + str(g.dotsRows))

        toEncode()

    if os.path.isfile("static/images/papertoprint.png"):
        return render_template('form_encode.html', image_path="static/images/papertoprint.png", message_path="../static/messages/printready.png")
    else:
        return render_template('form_encode.html', message_path="../static/messages/printready.png")

#============================
#【音声の確認】
@app.route("/toCheck", methods=["POST"])
def toCheck():
    print("***PeraPPera : play!")

    filepath = "static/sound/recorded.wav"

    if os.path.isfile(filepath):
        wav_obj = simpleaudio.WaveObject.from_wave_file(filepath)
        play_obj = wav_obj.play()
        play_obj.wait_done()  #再生終わるまで待機
        print("***PeraPPera : play_finished")
    else:
        print("***PeraPPera : no decoded audio data")
        return render_template('form_encode.html', image_path="static/images/papertoprint.png", message_path="../static/messages/nodatatoprint.png")

    return render_template('form_encode.html', image_path="static/images/papertoprint.png", message_path="../static/messages/printready.png")

#============================
#【プリント】
@app.route("/toPrint", methods=["POST"])
def toPrint():

    if os.path.isfile("static/images/papertoprint.png"): #あくまで条件分岐にファイルの有無を使用しているだけで、このpngファイル自体を印刷する訳ではない
        buf = BytesIO()
        g.paper.save(buf, 'PNG')

        p = subprocess.Popen('lpr', stdin=subprocess.PIPE)
        p.communicate(buf.getvalue())

        p.stdin.close()
        buf.close()
        print("***PeraPPera : print ready")
    else:
        print("***PeraPPera : no paper to print")
        return render_template('form_encode.html', image_path="static/images/papertoprint.png", message_path="../static/messages/nodatatoprint.png")

    return render_template('form_encode.html', image_path="static/images/papertoprint.png", message_path="../static/messages/printready.png")

#============================
#【抹消】
@app.route("/toDelete", methods=["POST"])
def toDelete():

    if os.path.isfile("static/sound/recorded.wav"):
        os.remove("static/sound/recorded.wav")
        print("***PeraPPera : deleted")
    else:
        print("***PeraPPera : file to delete not found")

    #画像が入ってるディレクトリごと消去→作成
    shutil.rmtree("static/images")
    os.mkdir("static/images")

    return render_template('form_encode.html', message_path="../static/messages/yourdatahasbeendeleted.png")

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
    app.run(host="0.0.0.0", port=18921, debug=True, threaded=True)
