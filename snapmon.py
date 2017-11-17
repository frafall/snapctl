#!/usr/bin/python
import snapcast
import json

srv = snapcast.SnapServer('192.133.64.10', debug=True)

while True:
   msg = srv.get()
   print json.dumps(msg, indent=3, sort_keys=True)
   
srv.close()

