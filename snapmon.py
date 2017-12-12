#!/usr/bin/python3
#
# Display metadata of playing streams
#
# Author: github.com/frafall
#
import sys
import os
import time
import signal
import functools
import logging
import argparse
import snapcast.control
import asyncio
import json

from concurrent.futures import CancelledError

#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
#logger = logging.getLogger(__name__)

def serverPort(service):
   try:
      server, port = service.split(':')

   except ValueError:
      server = service
      port   = snapcast.control.CONTROL_PORT

   else:
      port   = int(port)

   return server, port

def default(a,b):
   if a:
      return a
   return b
      
def tag(jtag, name, default=None):
   if(name in jtag):
      return jtag[name]
   return default

def run_cmd(loop, server, port):
   return (yield from snapcast.control.create_server(loop, server, port))

def main():
   verbose = 0

   def shutdown(signame):
      for task in asyncio.Task.all_tasks():
         task.cancel()

   def OnGroupUpdate(group):
      stream = snapserver.stream(group.stream)
      title = tag(stream.meta,'TITLE', '<unknown>')
      artist = tag(stream.meta,'ARTIST', '<unknown>')
      print("Zone '%s' playing '%s' by '%s'" %(group.friendly_name, title, artist))

   async def run_status(loop, snapserver):
      while True:
         await asyncio.sleep(1)

   # Parse arguments
   parser = argparse.ArgumentParser()
   parser.add_argument('-v', '--verbose', action='count', default=0)
   parser.add_argument('-s', '--server', default=os.environ.get('SNAPSERVER', '127.0.0.1'))

   args = parser.parse_args()
   server, port = serverPort(args.server)

   print("Connecting to %s port %d" %(server, port))
   loop = asyncio.get_event_loop()

   for signame in ('SIGINT', 'SIGTERM'):
      loop.add_signal_handler(getattr(signal, signame), functools.partial(shutdown, signame))

   try:
      snapserver = loop.run_until_complete(run_cmd(loop, server, port))

   except OSError:
      print("Can't connect to %s:%d" %(server, port))
      return

   for group in snapserver.groups:
      group.set_callback(OnGroupUpdate)

   try:
      loop.run_until_complete(run_status(loop, snapserver))

   except CancelledError:
      pass

   loop.close()

if __name__ == '__main__':
   main()
