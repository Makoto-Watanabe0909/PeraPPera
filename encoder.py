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
#【入力部分】
@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        print("Module Choice : " + str(request.form['modu']))
        print("Resolution : " + str(request.form['resoCol']) + "×" + str(request.form['resoRow']))
        g.moduleChoice = str(request.form['modu'])
        g.dotsColumns = int(str(request.form['resoCol']))
        g.dotsRows = int(str(request.form['resoRow']))

        return render_template('form_encode.html')
    else:
        return render_template('form_encode.html')

@app.route("/reloadProjection", methods=["POST"])
def reloadProjection():
    print("reload!")
    return render_template('form_encode.html', image_path="static/images/projection.png")

#============================
#【エンコード】
@app.route("/toEncode", methods=["POST"])
def toEncode():
    print("encode!")

    return render_template('form_encode.html')

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
