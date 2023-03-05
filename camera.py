#============================
#【定義】
import cv2
import Database
import numpy as np
from PIL import Image
import global_value as g
from flask import Flask, render_template
import os
import base64
import io
import time

#============================
#【セットアップ】
aruco = cv2.aruco
dictionary = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
parameters = aruco.DetectorParameters_create()

windowWidth = Database.windowWidth     #ウィンドウの幅
arucoSize = Database.arucoSize         #マーカのサイズ
waitkeyNum = Database.waitkeyNum       #読み取り時のカメラフレームのsleep数

#検知するマーカ番号
id0 = 0
id1 = 1
id2 = 2
id3 = 3

#使用するカメラのサイズが入る
camHeight = 0
camWidth = 0

#カメラの番号
DEVICE_ID = 0

#============================
#【カメラの制御】

class Camera(object):
    #【初期化】
    def __init__(self):
        self.video = cv2.VideoCapture(DEVICE_ID)

        camHeight = self.video.get(cv2.CAP_PROP_FRAME_WIDTH)
        camWidth = self.video.get(cv2.CAP_PROP_FRAME_HEIGHT)  #画像のサイズを取得
        print("camera initialized!")

    def __del__(self):
        self.video.release()

    #【映像処理】
    def get_frame(self):
        ret, image = self.video.read()
        global corners, ids, rejectedCandidates

        if ret:
            corners, ids, rejectedCandidates = aruco.detectMarkers(image, dictionary, parameters=parameters) #マーカーを全部検知
            markedImg = aruco.drawDetectedMarkers(image, corners, ids)
            list_ids = np.ravel(ids)  #検知できたマーカーの1次元リスト
            ret, frame = cv2.imencode('.jpg', markedImg)

            if (id0 in list_ids) and (id1 in list_ids) and (id2 in list_ids) and (id3 in list_ids): #全部検知できたら投影する

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
                pts2 = np.float32([(0,0), (0,g.dotsRows+2), (g.dotsColumns+2,g.dotsRows+2), (g.dotsColumns+2,0)])  #投影後の座標
                M = cv2.getPerspectiveTransform(pts1,pts2)
                #print("detected! / col : ", str(g.dotsColumns), ", row : ", str(g.dotsRows))
                global imgMain_toShow, imgMain_toProcess
                imgMain_toShow = cv2.warpPerspective(image, M, (g.dotsColumns+2, g.dotsRows+2), borderValue=(255,255,255)) #表示用
                imgMain_toProcess = cv2.warpPerspective(image, M, (g.dotsColumns+2, g.dotsRows+2), borderValue=(255,255,255)) #処理用

                #画像を書き出し
                img_name = "projection.png"
                cv2.imwrite(os.path.join("static/images/" + img_name), imgMain_toShow)
                g.isProjected = 1

                #time.sleep(3)
        else:
            frame = np.array(Image.open('image/temp.png'))
            print("no image from cam")

            self.video.release()
            self.video = cv2.VideoCapture(DEVICE_ID)


        return frame
