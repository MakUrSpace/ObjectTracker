import argparse
import cv2
import os
import json
from random import choice
from datetime import datetime, timedelta
import base64

from flask import Flask, render_template, Response


CAMERAS = []
app = Flask(__name__)


def capture_camera(cam_num):
    try:
        cam = cv2.VideoCapture(cam_num)
        retval, image = cam.read()
    finally:
        cam.release()
        cv2.destroyAllWindows()
    retval, buff = cv2.imencode('.jpg', image)
    b64jpg = base64.b64encode(buff)
    return b64jpg


def identify_cameras(device_numbers=list(range(6))):
    functional = []
    for dn in device_numbers:
        try:
            img = capture_camera(dn)
            functional.append(dn)
        except Exception as e:
            continue
    return functional


def gen_frames(camera_idx):
    assert int(camera_idx)  in CAMERAS, f"Invalid Camera: {camera_idx}. Valid Cameras: {CAMERAS}"

    while True:
        try:
            cap = cv2.VideoCapture(camera_idx)
            ret, cv2_im = cap.read()
        finally:
            cap.release()
            cv2.destroyAllWindows()
        if not ret:
            break

        retval, buff = cv2.imencode('.jpg', cv2_im)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buff.tobytes() + b'\r\n')
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


@app.route('/video_feed/<camera_idx>')
def video_feed(camera_idx):
    #Video streaming route. Put this in the src attribute of an img tag
    return Response(gen_frames(int(camera_idx)), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/still/<camera_idx>')
def still(camera_idx):
    return Response(capture_camera(int(camera_idx)))


@app.route('/camera_list')
def camera_list():
    return Response(json.dumps(CAMERAS).encode())


@app.route('/')
def index():
    """Video streaming home page."""
    return render_template('index.html', cameras=CAMERAS)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    CAMERAS = identify_cameras()
    print(f"Supporting Cameras: {CAMERAS}")
    app.run(debug=True, host="0.0.0.0", use_reloader=False)

