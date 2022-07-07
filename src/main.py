from flask import Flask, jsonify, request

import cv2
import threading
import time

import camera_io.cameraIO as cameraIO
import multi_thread_data_processing.multiThreadDataProcessing as mtl
from data_model.dataModel import Config

import init_cameras

app = Flask(__name__)
cameras = cameraIO.AllCameras()
cameraDisplay = cameraIO.CameraDisplay("Video", cameras.camera_data)

def main():
    data_display = mtl.DataSink(cameras.data_output, cameraDisplay)
    data_display.start()
    threading.Thread(target=app_run).start()
    time.sleep(1)
    threading.Thread(target=start_cameras).start()

def app_run():
    app.run(debug=False, threaded=True)

def start_cameras():
    init_cameras.start()

def get_cameras():
    result = cameras.cameras_to_dict()
    return jsonify(result)

@app.route('/cameras/get', methods=['GET'])
def get_cameras_rest():
    return get_cameras()


@app.route('/cameras/activate', methods=['GET'])
def stop_start_cameras_rest():
    index: str = request.args.get("index")
    active: str = request.args.get("active")
    if active.__eq__("true"):
        cameras.start_camera(int(index))
        return "camera {} turned on".format(index), 200
    elif active.__eq__("false"):
        cameras.stop_camera(int(index))
        return "camera {} turned off".format(index), 200
    else:
        return 'bad request!', 400


@app.route('/cameras/create', methods=['GET'])
def create_camera_rest():
    try:
        index: int = int(request.args.get("index"))
        fps: float = float(request.args.get("fps"))
        x: int = int(request.args.get("x"))
        y: int = int(request.args.get("y"))
        angle: float = float(request.args.get("angle"))
    except:
        return "wrong arguments", 400
    print("Creating camera with index {}, fps {}, and starting point {},{}".format(index, fps, x, y))
    try:
        cameras.add_camera(index, fps, x, y, angle)
    except:
        return "index {} does not exist".format(index), 500
    return "camera {} created".format(index), 200


@app.route('/cameras/update', methods=['GET'])
def update_camera_rest():
    try:
        index: int = int(request.args.get("index"))
        fps: float = float(request.args.get("fps"))
        x: int = int(request.args.get("x"))
        y: int = int(request.args.get("y"))
        angle: float = float(request.args.get("angle"))
    except:
        return "wrong arguments", 400
    if index not in cameras.indexes:
        return "camera {} does not exist".format(index), 500
    lock = threading.Lock()
    lock.acquire(blocking=True, timeout=-1)
    camera = cameras.all_cameras.get(index)
    camera.fps = fps
    camera.data_getter.period = 1/fps
    camera.x = x
    camera.y = y
    camera.angle = angle
    cameras.camera_data[index] = x, y, angle, camera.resolution, camera.cals_display_points()
    lock.release()
    return "camera {} updated".format(index), 200


@app.route('/cameras/free', methods=['GET'])
def get_available_indexes_rest():
    config = Config()
    result = []
    for index in range(config.get_max_search_index()):
        if index not in cameras.indexes:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                result.append(index)
                cap.release()
    return "available indexes: {}".format(result), 200


@app.route('/cameras/resolutions', methods=['GET'])
def get_available_resolutions_rest():
    config = Config()
    result = {}
    for index in range(config.get_max_search_index()):
        if index not in cameras.indexes:
            cap = cv2.VideoCapture(index)
            if cap.isOpened():
                result[index] = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
                cap.release()
    return "available indexes and resolutions: {}".format(result), 200

@app.route('/objects/pos', methods=['GET'])
def get_all_objects_pos():
    return jsonify(cameraDisplay.detected_objects_centers), 200

@app.route('/object/pos_with_id', methods=['GET'])
def get_object_pos():
    try:
        index: int = int(request.args.get("index"))
    except:
        return "wrong argument", 400
    try:
        position = cameraDisplay.average_position[index]
    except:
        return f"object {index} not detected", 500
    try:
        my_json = jsonify(position)
    except:
        return "could not jsonify", 400
    return my_json, 200

if __name__ == "__main__":
    main()


# https://forum.opencv.org/t/camera-stops-working-after-about-an-hour-of-working/8098