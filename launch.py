#!/usr/bin/env python3
from app import app
from app import manager
from app import main_bulltin_board

import sys
import time
import logging
import json
from mptools import (
    init_signals,
    default_signal_handler,
    MainContext,
    EventMessage,
    ProcWorker,
    TimerProcWorker,
    QueueProcWorker,
)

######################################
# Workers
######################################

## Server Worker
class ServerWorker(ProcWorker):
    def init_args(self, args):
        self.tried_shutdown = False

    def startup(self):
        pass

    def shutdown(self):
        # TODO Graceful shutdown
        pass
    
    def main_func(self):
        if not self.shutdown_event.is_set():
            app.run(host="0.0.0.0", port=5000, debug=True,threaded=True, use_reloader=False)
            self.log(logging.INFO, f"Server Active")

## Camera Worker
import cv2
import time 

class CameraWorker(ProcWorker):
    def init_args(self, args):
        self.shared_dict=main_bulltin_board

    def startup(self):
        self.stream = cv2.VideoCapture(0)
        self.grabbed, self.frame = self.stream.read()
        self.log(logging.INFO, f"Camera Worker Active")

    def shutdown(self):
        self.stream.release()

    def main_func(self):
        while not self.shutdown_event.is_set():
            (self.grabbed, self.frame) = self.stream.read()
            self.shared_dict['video']=[time.time(),self.frame]
            time.sleep(1/5)

######################################
# Handlers
######################################

#  ---- Genral Functions
def request_handler(event, reply_q, main_ctx):
    if event.msg_type == "REQUEST":
        main_ctx.log(logging.DEBUG, f"request_handler - '{event.msg}'")
        if event.msg == "REQUEST END":
            main_ctx.log(logging.DEBUG, "request_handler - queued END event")
            main_ctx.event_queue.safe_put(EventMessage("request_handler", "END", "END"))

        reply = f'REPLY {event.id} {event.msg}'
        reply_q.safe_put(reply)
    if event.msg_type == "COMMAND":
        reply_q.safe_put(event)

########################################
# Main Launch
########################################
def main(die_in_secs):
    with MainContext() as main_ctx:
        if die_in_secs:
            die_time = time.time() + die_in_secs
            main_ctx.log(logging.DEBUG, f"Application die time is in {die_in_secs} seconds")
        else:
            die_time = None
            
        init_signals(main_ctx.shutdown_event, default_signal_handler, default_signal_handler)

        # Queues
        send_q = main_ctx.MPQueue()
        reply_q = main_ctx.MPQueue()
        main_ctx.Proc("CameraWorker", CameraWorker)
        main_ctx.Proc("Server", ServerWorker)

        while not main_ctx.shutdown_event.is_set():
            if die_time and time.time() > die_time:
                raise RuntimeError("Application has run too long.")
            event = main_ctx.event_queue.safe_get()
            if not event:
                continue
            elif event.msg_type == "STATUS":
                send_q.put(event)
            elif event.msg_type == "OBSERVATION":
                send_q.put(event)
            elif event.msg_type == "ERROR":
                send_q.put(event)
            elif event.msg_type == "REQUEST":
                request_handler(event, reply_q, main_ctx)
            elif event.msg_type == "FATAL":
                main_ctx.log(logging.INFO, f"Fatal Event received: {event.msg}")
                break
            elif event.msg_type == "END":
                main_ctx.log(logging.INFO, f"Shutdown Event received: {event.msg}")
                break
            else:
                main_ctx.log(logging.ERROR, f"Unknown Event: {event}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Change logging level here
    die_in_secs = float(sys.argv[1]) if sys.argv[1:] else 0
    main(die_in_secs)