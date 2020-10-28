from app import app
from flask import request, Response
import cv2
from app import main_bulltin_board

# Video Pagination
@app.route('/video')
def video():
    def gen():
        while True:
            frame=cv2.resize(main_bulltin_board["video"][1], (int(640), int(480)))
            encoded, buffer = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + bytearray(buffer)  + b'\r\n')
    return Response(gen(),mimetype='multipart/x-mixed-replace; boundary=frame')


