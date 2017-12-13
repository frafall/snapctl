#!/usr/bin/python3
#
# Show status of a snapserver
#
# Author: github.com/frafall
#
import os
import sys
import logging
import argparse
import asyncio
import json
import snapcast.control

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

def run_cmd(loop, server, port):
   return (yield from snapcast.control.create_server(loop, server, port))

def main():
   verbose = 0

   # Verbose output
   def vprint(str):
      if verbose > 0:
         print(str)

   def setalt(a,b):
      if a:
         return a
      return b
      
   def tag(jtag, name, default=None):
      if(name in jtag):
         return jtag[name]
      return default

   # Parse arguments
   parser = argparse.ArgumentParser()
   parser.add_argument('-v', '--verbose', action='count', default=0)
   parser.add_argument('-d', '--debug', action='store_true')
   parser.add_argument('-s', '--server', default=os.environ.get('SNAPSERVER', '127.0.0.1'))

   args = parser.parse_args()
   verbose = args.verbose
   server, port = serverPort(args.server)

   vprint("Connecting to %s port %d" %(server, port))
   loop = asyncio.get_event_loop()
   
   try:
      snapserver = loop.run_until_complete(run_cmd(loop, server, port))

   except OSError:
      print("Can't connect to %s:%d" %(server, port))

   else:
      print("\nZones:")
      for group in snapserver.groups:
         if verbose > 0:
            print("   [%s] name='%s' stream='%s'" %(group.identifier, group.name, group.stream))
         else:
            name = setalt(group.name, '<nameless>')
            print("   %s (%s)" %(name, group.stream))

         for id in group.clients:
            client = snapserver.client(id)
            if verbose > 0:
               print("      [%s] %s" %(client.identifier, client.friendly_name))
            else:
               print("      %s" %(client.friendly_name))
         print()

      print("Streams:")
      for stream in snapserver.streams:
         print("   [%s] %s" %(stream.status, stream.name))
         if(stream.status != 'idle'):
            title = tag(stream.meta, 'TITLE')
            artist = tag(stream.meta, 'ARTIST')
            print("      artist: %s" %(artist))
            print("       title: %s" %(title))


if __name__ == '__main__':
   main()
