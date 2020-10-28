from flask import Flask, request

app = Flask(__name__)

######################################
# Bulltin
######################################
import multiprocessing
manager = multiprocessing.Manager()

## Shared Memory
main_bulltin_board = manager.dict()

## SERVER STUFF
# Prevent cached responses
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, public, max-age=0"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

from app import video_routes

