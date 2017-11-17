#!/usr/bin/python
import os, socket
import argparse
import telnetlib
import json
import time
import threading
import queue


class SnapServer(threading.Thread):
   reqId = 1

   def __init__(self, server=None, debug=None):
      super(SnapServer, self).__init__()
      self.debug = debug

      # If no server argument use environment,
      # else fallback to localhost
      if(server is None):
         server = os.environ.get('SNAPSERVER', '127.0.0.1')

      if self.debug:
         print('Debug: Connecting to %s' %(server))
      self.socket = telnetlib.Telnet(server, 1705)

      # Setup reader thread
      self.t_stop = threading.Event()
      self.input  = queue.Queue()
      self.start()

   def close(self):
      self.t_stop.set();
      s = self.socket.get_socket()
      s.shutdown(socket.SHUT_RD)
      self.join()

   def type(self, msg):
      if 'method' in msg:
         return '%s' %(msg['method'])
      if 'id' in msg:
         return 'response[%d]' %(msg['id'])
      return 'unknown'

   # Read response from snapserver and queue it
   def run(self):
      while (not self.t_stop.is_set()):
         try:
            response = self.socket.read_until("\r\n", 2)

         except:
            pass
            
         else:
            if response:
               msg = json.loads(response)
               self.input.put(msg) 
               if self.debug:
                  print('Debug: message queued (%s)' %(self.type(msg)))

   # Send to server
   def send(self, request):
      id = self.reqId
      self.reqId = (self.reqId + 1) % 10000

      request['jsonrpc'] = '2.0'
      request['id'] = id
      self.socket.write(json.dumps(request) + "\r\n")
  
      if self.debug:
         print('Debug: sendt message: %s' %(request))

      return id

   # Pop from queue
   def get(self, block=True, timeout=None):
      msg = self.input.get(block, timeout)
      if msg and self.debug:
         print('Debug: reading queue (%s)' %(self.type(msg)))
      return msg

   # Synchronous query
   def query(self, request):
      id = self.send(request)

      # Add some timeout ?
      while True:
         msg = self.get()

         if self.debug:
            print('Debug: received message: (%s)' %(self.type(msg)))

         if('id' in msg and msg['id'] == id):
            break

      if self.debug:
         print('Debug: response %d found' %(id))
      return msg

   def GetStatus(self):
      return self.query({'method': 'Server.GetStatus'})


def main():
   srv = SnapServer(debug=True)
   response = srv.GetStatus()
   print(response)
   srv.close()

if __name__ == '__main__':
   main()

