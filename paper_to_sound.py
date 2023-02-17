#　python paper_to_sound.py
import Database
import Nc
import os
import sys
import time
import threading
import math
import numpy as np
import cv2
import simpleaudio
import tkinter as tk
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageOps
from io import BytesIO
from pickletools import pydict
from re import A
from tty import CFLAG
from tkinter import filedialog
from tkinter import ttk
from decimal import Decimal, ROUND_HALF_UP, ROUND_HALF_EVEN
from camera import Camera


print("==========================================================================")

#マーカー関連
aruco = cv2.aruco
dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
parameters = aruco.DetectorParameters_create()

windowWidth = Database.windowWidth     #ウィンドウの幅
arucoSize = Database.arucoSize         #マーカのサイズ
ncSoundRows = Database.ncSoundRows     #ノイズキャンセリング用の無音地帯の高さ
waitkeyNum = Database.waitkeyNum       #読み取り時のカメラフレームのsleep数

cameraJobId = None  #カメラ更新の定期便を停止するためのID

#デコード本編
def decodeStart():
    global cameraJobId
    root.after_cancel(cameraJobId)  #カメラと画像処理を一時停止

    #GUIから情報を取得
    fname = boxTitle.get()
    samplingRate = int(boxSR.get())
    moduleChoice = boxMdl.get()
    dotsColumns = int(boxCo.get())
    dotsRows = int(boxRo.get())

    #downsample率を計算（数値が大きいほど大きくサンプルされる。）
    downsample = int(48000/samplingRate)

    buffer = []  #最後に音声データに変えるバッファ
    print("hei=", dotsRows, " wid=", dotsColumns)

    #色→音の肝心な部分
    def colorToSound(mainORnc):
        if mainORnc == "decoded":
            rowsNum = dotsRows
            columnsNum = dotsColumns
        elif mainORnc == "forNC":
            rowsNum = ncSoundRows
            columnsNum = dotsColumns

        forThreeCount = 0 #実験用　終わったら消す

        for i in range(rowsNum-1): #端っこは白が混ざっていて読み取りたくないので読み取る行を減らしている。
            convertVar.set(int((i/(rowsNum-1))*100))#進捗バーの更新
            for j in range(columnsNum-1): #端っこは白が混ざっていて読み取りたくないので読み取る列を減らしている。
                pX = int(j+2)#端っこは白が混ざっていて読み取りたくないので読み取る列を減らしている。
                pY = int(i+2)

                print()
                if mainORnc == "decoded":
                    rawcolor = imgMain[pY,pX]  #色の取得
                elif mainORnc == "forNC":
                    rawcolor = imgNC[pY,pX]  #色の取得

                #音波に直してバッファに追加（ダウンサンプルしてる場合は同じ数値をその分だけ書き込む）
                if not (moduleChoice == "ThreeToOne"):
                    for n in range(int(downsample)):
                        print(eval("Database." + moduleChoice + "CS(rawcolor)"))
                        buffer.append(eval("Database." + moduleChoice + "CS(rawcolor)"))
                else:  #3色1マスパターン
                    for k in range(3):
                        for n in range(int(downsample)):
                            buffer.append(eval("Database." + moduleChoice + "CS(rawcolor[" + str(k) + "])"))
                            if samplingRate == 36000:
                                if (forThreeCount % 2 == 0):
                                    buffer.append(eval("Database." + moduleChoice + "CS(rawcolor[" + str(k) + "])"))
                                    forThreeCount += 1
                            print(".")

                print(mainORnc + " processed pix : ", pX, "," , pY)
                print("color : ", rawcolor)
                print("==========================")

        #溜まったデータをwavに変換
        sr = 48000
        filepath = fname + "->" + mainORnc + ".wav"
        _format = "WAV"
        subtype = 'PCM_24'
        sf.write(filepath,  buffer, sr, format=_format, subtype=subtype)

    colorToSound("decoded")  #メインの音声を変換→ファイルに

    #ノイズキャンセリング
    if ncONOFF.get() :
        buffer = []
        colorToSound("forNC")  #NC用音声を変換→ファイルに

        #本編
        Nc.execute(fname)

        #不要なファイルを削除
        os.remove("./" + fname + "->decoded.wav")
        os.remove("./" + fname + "->forNC.wav")

    root.after(waitkeyNum, cameraUpdate)  #カメラと画像処理を再開
    btnPlay['state'] = 'normal'  #再生ボタンを押せるように
    print("all processes ended")

def radio_click():
    global cameraJobId
    root.after_cancel(cameraJobId)  #
    cameraUpdate()

def toDecordStart():  #デコードの時に別スレッドを建てる関数（進捗バーの垂直同期のため）
    threadDecord = threading.Thread(target=decodeStart)
    threadDecord.start()

def toPlay():  #読み込んだファイルの再生
    fname = boxTitle.get()
    generatedSoundfilePath = os.getcwd() + "/" + fname + "->decoded.wav"  #パス名を生成

    wav_obj = simpleaudio.WaveObject.from_wave_file(generatedSoundfilePath)
    play_obj = wav_obj.play()
    play_obj.wait_done()  #再生終わるまで待機

#＝＝＝＝＝＝＝＝＝＝＝＝＝＝＝GUIを制作＝＝＝＝＝＝＝＝＝＝＝＝＝＝

#カメラの用意
cap = cv2.VideoCapture(1)
camWidth = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
camHeight = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)

#GUIに描画するカメラ映像の縦横ピクセル
camWidthInWindow = int(camWidth/3)
camHeightInWindow = int(camWidthInWindow*(camHeight/camWidth))

root = tk.Tk()
root.title(u"Decoder")
root.geometry(str(int(windowWidth)) + "x" + str(int(camHeightInWindow+300)))
#root.resizable(False, False)

#曲名（ファイル名になる）
labelTitle = tk.Label(text='名前')
labelTitle.grid(row= 0, column=0)  #GRID
boxTitle = tk.Entry(width=20)
boxTitle.grid(row= 0, column=1)  #GRID
boxTitle.insert(tk.END,"title")

#サンプリングレート
labelSR = tk.Label(text='サンプリングレート')
labelSR.grid(row= 1, column=0)  #GRID
boxSR = tk.Entry(width=20)
boxSR.grid(row= 1, column=1)  #GRID
boxSR.insert(tk.END,"48000")

#モジュールの選択
labelMdl = tk.Label(text='モジュール')
labelMdl.grid(row= 2, column=0)  #GRID
boxMdl = tk.Entry(width=20)
boxMdl.grid(row= 2, column=1)  #GRID
boxMdl.insert(tk.END,"ThreeToOne")

#解像度
labelCo = tk.Label(text='解像度（ヨコ）')
labelCo.grid(row= 3, column=0)  #GRID
boxCo = tk.Entry(width=20)
boxCo.grid(row= 3, column=1)  #GRID
boxCo.insert(tk.END,"80")
labelRo = tk.Label(text='解像度（タテ）')
labelRo.grid(row= 4, column=0)  #GRID
boxRo = tk.Entry(width=20)
boxRo.grid(row= 4, column=1)  #GRID
boxRo.insert(tk.END,"600")

ncONOFF = tk.BooleanVar()
ncONOFF.set(False)
#chk_ncOFF = tk.Checkbutton(root, text='ノイズキャンセリング', variable = ncONOFF)
#chk_ncOFF.grid(row= 5, column=0)  #GRID

#outputDebugPic = tk.BooleanVar()
#outputDebugSound = tk.BooleanVar()
#chk_outputDebugPic = tk.Checkbutton(root, text='デバッグ用の画像も出力する', variable = outputDebugPic)
#chk_outputDebugPic.grid(row= 7, column=0)  #GRID
#chk_outputDebugSound = tk.Checkbutton(root, text='デバッグ用の音声も出力する', variable = outputDebugSound)
#chk_outputDebugSound.grid(row= 8, column=0)  #GRID

#書き出しボタン
btnDecode = tk.Button(root, text='DECODE', command=toDecordStart)
btnDecode.grid(row= 10, column=0)  #GRID
btnDecode['state'] = 'disabled'

#進捗バー
convertVar = tk.IntVar(root)
pbForConvert = ttk.Progressbar(root,  maximum=100,mode="determinate", variable = convertVar)
pbForConvert.grid(row= 11, column=0)  #GRID

#メイン or NCのラジオ
#読み取り用　メインの音声を読み取るときと、NCを読み取るときとでモードを切り替える
phase = tk.IntVar(value = 0)
radioMain = tk.Radiobutton(root, text = "メイン音声",
                        command = radio_click,
                        variable = phase,
                        value = 0)
radioNC = tk.Radiobutton(root, text = "ノイズキャンセリング用音声",
                        command = radio_click,
                        variable = phase,
                        value = 1)
#radioMain.grid(row= 12, column=1)  #GRID
#radioNC.grid(row= 12, column=2)  #GRID

#カメラからの画像
camCanvas = tk.Canvas(root, width=camWidthInWindow, height=camHeightInWindow)
camCanvas.grid(row= 13, column=0)  #GRID

#投影した画像_mains
projectionCanvas_main = tk.Canvas(root, width=camHeightInWindow/2, height=camHeightInWindow/2)
projectionCanvas_main.grid(row= 13, column=1)  #GRID

#投影した画像_nc
projectionCanvas_nc = tk.Canvas(root, width=camWidthInWindow/5, height=camHeightInWindow)
projectionCanvas_nc.grid(row= 13, column=2)  #GRID

#再生ボタン
btnPlay = tk.Button(root, text='PLAY', command=toPlay)
btnPlay.grid(row= 14, column=0)  #GRID
btnPlay['state'] = 'disabled'

def cameraUpdate():
        if phase.get() == 0:
            id0 = 0
            id1 = 1
            id2 = 2
            id3 = 3
        if phase.get() == 1:
            id0 = 246
            id1 = 247
            id2 = 248
            id3 = 249

        ret, frame = cap.read()

        global corners, ids, rejectedCandidates, cameraJobId

        corners, ids, rejectedCandidates = aruco.detectMarkers(frame, dictionary, parameters=parameters) #マーカーを全部検知
        markedImg = aruco.drawDetectedMarkers(frame, corners, ids)
        list_ids = np.ravel(ids)  #検知できたマーカーの1次元リスト

        frameToShow = cv2.resize(markedImg, (camWidthInWindow, camHeightInWindow))  #表示用の画像は縮小する
        frameToShow = cv2.cvtColor(frameToShow, cv2.COLOR_BGR2RGB)
        root.photo = ImageTk.PhotoImage(image = Image.fromarray(frameToShow))
        camCanvas.create_image(0,0, image= root.photo, anchor = tk.NW)

        #print("detecting......")

        if (id0 in list_ids) and (id1 in list_ids) and (id2 in list_ids) and (id3 in list_ids): #全部検知できたら投影する
            dotsColumns = int(boxCo.get())
            dotsRows = int(boxRo.get())

            indexUL = np.where(ids == id0)[0][0]
            indexUR = np.where(ids == id1)[0][0]
            indexBL = np.where(ids == id2)[0][0]
            indexBR = np.where(ids == id3)[0][0]

            pointUL = (int(corners[indexUL][0][2][0]),int(corners[indexUL][0][2][1]))
            pointBL = (int(corners[indexBL][0][1][0]),int(corners[indexBL][0][1][1]))
            pointBR = (int(corners[indexBR][0][0][0]),int(corners[indexBR][0][0][1]))
            pointUR = (int(corners[indexUR][0][3][0]),int(corners[indexUR][0][3][1]))

            #投影するパートだ 参考 : https://qiita.com/mo256man/items/27d0a44071aee5f06933
            pts1 = np.float32([pointUL, pointBL, pointBR, pointUR])  #投影前の座標
            pts2 = np.float32([(0,0), (0,dotsRows+2), (dotsColumns+2,dotsRows+2), (dotsColumns+2,0)])  #投影後の座標

            M = cv2.getPerspectiveTransform(pts1,pts2)
            global imgMain, imgNC

            #投影した画像をGUIに表示
            projectionWidthInWindow = int(camHeightInWindow * float(dotsColumns/dotsRows))
            if phase.get() == 0:
                imgMain = cv2.warpPerspective(frame, M, (dotsColumns+2, dotsRows+2), borderValue=(255,255,255))
                imgMain_toProcess = cv2.warpPerspective(frame, M, (dotsColumns+2, dotsRows+2), borderValue=(255,255,255))
                img2ToShow = cv2.resize(imgMain_toProcess, (int(camHeightInWindow/2), int(camHeightInWindow/2)))
                img2ToShow = cv2.cvtColor(img2ToShow, cv2.COLOR_BGR2RGB)
                root.photo2 = ImageTk.PhotoImage(image = Image.fromarray(img2ToShow))
                projectionCanvas_main.create_image(0,0, image= root.photo2, anchor = tk.NW)
                btnDecode['state'] = 'normal'  #デコードボタンを押せるように

            elif phase.get() == 1:
                imgNC = cv2.warpPerspective(frame, M, (dotsColumns+4, dotsRows+4), borderValue=(255,255,255))
                img2ToShow = cv2.resize(imgNC, (projectionWidthInWindow, int(projectionWidthInWindow * (float)(ncSoundRows/dotsColumns))))
                img2ToShow = cv2.cvtColor(img2ToShow, cv2.COLOR_BGR2RGB)
                root.photo3 = ImageTk.PhotoImage(image = Image.fromarray(img2ToShow))
                projectionCanvas_nc.create_image(0,0, image= root.photo3, anchor = tk.NW)

        cameraJobId = root.after(waitkeyNum, cameraUpdate)  #「cameraJobId」は定期便を解約する時に使うらしい

cameraUpdate()
root.mainloop()
