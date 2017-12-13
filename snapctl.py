#!/usr/bin/python3
"""
Snapcast control

Control snapcast setup.
  - add/delete/rename groups (zones)
  - add/rename clients (to zones)
  - show group (zone)
  - show streams

Author: github.com/frafall
"""
import sys
import os
import logging
import argparse
import asyncio
import json

import snapcast.control

def setdefault(a,b):
   if a:
      return a
   return b

class SnapController(object):
   """Snapcast controller"""

   def __init__(self, serverstring, verbose=0, debug=False):
      self._verbose = verbose
      self._debug = debug
  
      # Setup logging
      self._log = logging.getLogger('SnapController')
      if self._debug:
         logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

      # Parse the server string
      try:
         self._host, self._port = serverstring.split(':')

      except ValueError:
         self._host = serverstring
         self._port = snapcast.control.CONTROL_PORT

      else:
         self._port   = int(self._port)

      self._log.info('connecting to snapserver on %s:%s', self._host, self._port)

      self._loop = asyncio.get_event_loop()
      self._snapserver = self._loop.run_until_complete(self._update_status())

   # Stream information
   def showStream(self, stream, meta=False, multiline=True):
      if(type(stream) is str):
         stream = self._snapserver.stream(stream)
      print('[%s] %s' %(stream.status, stream.name))
      if meta and stream.status != 'idle':
         meta = stream.meta
         print(meta)

   def showAllStreams(self, meta=False):
      for stream in self._snapserver.streams:
         self.showStream(stream, meta=meta, multiline=False)

   # Group information
   def showGroup(self, group, multiline=True):
      if(type(group) is str):
         try:
            group = self._snapserver.group(group)

         except KeyError:
            for g in self._snapserver.groups:
               if(g.name == group):
                  group = g
                  break            

            if(type(group) is str):
               raise
 
      groupname = setdefault(group.name, '<no-name>')
  
      if self._verbose:
         print('[%s] %s, stream %s' %(group.identifier, groupname, group.stream))
      else:
         print('%s, stream %s' %(groupname, group.stream))

   def showAllGroups(self):
      for group in self._snapserver.groups:
         self.showGroup(group, multiline=False)

   #
   # Update functions
   #
   def _update_status(self):
      return (yield from snapcast.control.create_server(self._loop, self._host, self._port))

#
# Snapctl main, parser and options
#
def main():

   # Parse arguments
   parser = argparse.ArgumentParser(
      description='Control the Snapcast multi-room system.'
   )
   parser.add_argument('-v', '--verbose', action='count', default=0)
   parser.add_argument('-d', '--debug', action='store_true')
   parser.add_argument('-s', '--server', default=os.environ.get('SNAPSERVER', '127.0.0.1:1705'))
   subparsers = parser.add_subparsers(help='subparsers')
   
   #
   # The group command
   #
   parser_group = subparsers.add_parser('group')
   group_sub = parser_group.add_subparsers()

   # snapctl group show <nameorid>
   parser_group_show = group_sub.add_parser('show', help='Display information about one or all groups')
   parser_group_show.set_defaults(showgroup=True)
   parser_group_show.add_argument('nameorid', nargs='*', help='Name or id of group(s)')

   # snapctl group add <name> 
   parser_group_add = group_sub.add_parser('add', help='Add a new group')
   parser_group_add.set_defaults(addgroup=True)
   #parser_group.add_argument('nameorid', action='store', help='name of group to add')

   # snapctl group del <nameorid> 
   parser_group_del = group_sub.add_parser('delete', help='Delete a group')
   parser_group_del.set_defaults(delgroup=True)

   # snapctl group rename <nameorid> <name>
   parser_group_ren = group_sub.add_parser('rename', help='Rename a group')
   parser_group_ren.set_defaults(rengroup=True)

   #
   # The stream command
   #
   parser_stream = subparsers.add_parser('stream')
   stream_sub = parser_stream.add_subparsers()

   # snapctl stream show <nameorid>
   parser_stream_show = stream_sub.add_parser('show', help='Show one or all streams')
   parser_stream_show.set_defaults(showstream=True)
   parser_stream_show.add_argument('nameorid',nargs='*')
   parser.add_argument('-m', '--meta', action='store_true', default=False)

   #
   # The client command
   #
   parser_client = subparsers.add_parser('client')
   client_sub = parser_client.add_subparsers()

   # snapctl client show <nameorid>
   parser_client_show = client_sub.add_parser('show', help='Show a client')
   parser_client_show.set_defaults(showclient=True)

   # snapctl client rename <nameorid> <name>
   parser_client_ren = client_sub.add_parser('rename', help='Rename a client')
   parser_client_ren.set_defaults(renclient=True)

   # Do the parse
   args = parser.parse_args()

   # Setup controller
   try:
      controller = SnapController(args.server, verbose=args.verbose, debug=args.debug)

   except OSError:
      print("Can't connect to %s" %(args.server))
      return

   # Show one or all streams
   if('showstream' in args and args.showstream):
      if args.nameorid:
         for nameorid in args.nameorid:
            controller.showStream(nameorid, meta=args.meta)
      else:
         controller.showAllStreams(meta=args.meta)

   # Show one or more groups
   elif('showgroup' in args and args.showgroup):
      if args.nameorid:
         for nameorid in args.nameorid:
            controller.showGroup(nameorid)
      else:
         controller.showAllGroups()

   # No arguments given, display help
   else:
      parser.print_help()

if __name__ == '__main__':
   main()

