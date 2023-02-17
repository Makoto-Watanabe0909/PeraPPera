import cv2
import numpy as np

windowWidth = 1000

waitkeyNum = 10  #読み取り時のカメラフレームのsleep数
picDownsize = 5  #カメラフレームの表示のサイズ

#ドットについて
ncSoundRows = 100   #ノイズキャンセリング用の無音地帯の高さ

#紙の様式について
marginPaper = 10   #紙の上下左右の余白
marginColor = (200, 200, 200)  #余白の色

#Arucoマーカについて
arucoSize = 16  #サイズ

#################################################################################

#「redRose」レッドスケールで表現
def RedRoseSC(raw):  #音→色
    r = (raw+1)*256/2  #-1~1 →　0~256
    g = 0
    b = 0
    return int(r), int(g), int(b)

def RedRoseCS(raw):  #色→音
    a = (2*raw[2]/256)-1
    return a

#「blueEyes」ブルースケールで表現
def BlueEyesSC(raw):  #音→色
    r = 0
    g = 0
    b = (raw+1)*256/2  #-1~1 →　0~256
    return int(r), int(g), int(b)

def BlueEyesCS(raw):  #色→音
    a = (2*raw[0]/256)-1
    return a

#「greenDollar」グリーンスケールで表現
def GreenDollarSC(raw):  #音→色
    r = 0
    g = (raw+1)*256/2  #-1~1 →　0~256
    b = 0
    return int(r), int(g), int(b)

def GreenDollarCS(raw):  #色→音
    a = (2*raw[1]/256)-1
    print(a.dtype)
    return a

#「gradatedGray」グレースケールで表現
def GradatedGraySC(raw):  #音→色
    r = (raw+1)*256/2  #-1~1 →　0~256
    g = (raw+1)*256/2  #-1~1 →　0~256
    b = (raw+1)*256/2  #-1~1 →　0~256
    return int(r), int(g), int(b)

def GradatedGrayCS(raw):  #色→音
    b = (2*raw[0]/256)-1
    g = (2*raw[1]/256)-1
    r = (2*raw[2]/256)-1
    return (b + g + r)/3

#「Huemanism」色相に対応
def HuemanismSC(raw):  #音→色
    h = (raw+1)*180/2    #-1~1 →　0~180
    s = 255
    v = 255
    bgr = cv2.cvtColor(np.array([[[h, s, v]]], dtype=np.uint8), cv2.COLOR_HSV2BGR)[0][0]
    return int(bgr[0]), int(bgr[1]), int(bgr[2])

def HuemanismCS(raw):  #色→音
    hsv = cv2.cvtColor(np.array([[[raw[0], raw[1], raw[2]]]], dtype=np.uint8), cv2.COLOR_BGR2HSV)[0][0]
    a = hsv[0].astype(np.int32)
    return a

#「ThreeToOne」3色を1マスで
def ThreeToOneSC(raw):  #音→色
    n = (raw+1)*256/2  #-1~1 →　0~256
    return n

def ThreeToOneCS(raw):  #色→音
    n = (2*raw/256)-1
    return n
