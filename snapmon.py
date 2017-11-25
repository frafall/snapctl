#!/usr/bin/python
import signal
import snapcast
import queue
import json

class State:
   terminate = False

   def handler(self, signum, frame):
      signal.signal(signum, signal.SIG_IGN)
      self.terminate = True

   def __init__(self):
      signal.signal(signal.SIGINT, self.handler)


state = State()
srv = snapcast.SnapServer(debug=True)

while not state.terminate:
   msg = False

   try:
      msg = srv.get(timeout=1)

   except queue.Empty:
      pass

   if msg:
      print(json.dumps(msg, indent=3, sort_keys=True))
   
srv.close()

