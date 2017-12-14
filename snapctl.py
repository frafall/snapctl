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
      if meta and stream.status != 'idle':
         meta = stream.meta
         artist = setdefault(meta['ARTIST'], '-unknown-')
         title = setdefault(meta['TITLE'], '-unknown-')
         print("%s playing '%s' by %s" %(stream.name, title, artist))
      else:  
         print('%s' %(stream.name))

   def showAllStreams(self, meta=False):
      for stream in self._snapserver.streams:
         self.showStream(stream, meta=meta, multiline=False)

   # Client information
   def showClient(self, client, multiline=True):
      if(type(client) is str):
         client = self._snapserver.client(client)

      clientname = setdefault(client.name, '-noname-')

      if self._verbose:
         print('[%s] %s' %(client.identifier, clientname))
      else:
         print('%s' %(clientname))

   def showAllClients(self):
      for client in self._snapserver.clients:
         self.showClient(client, multiline=False)

   # Group information
   def showGroup(self, group, multiline=True):
      if(type(group) is str):
         group = self._groupByNameOrId(group)

      groupname = setdefault(group.name, '-noname-')
  
      if self._verbose:
         print('[%s] %s, stream %s' %(group.identifier, groupname, group.stream))
      else:
         print('%s, stream %s' %(groupname, group.stream))

   def showAllGroups(self):
      for group in self._snapserver.groups:
         self.showGroup(group, multiline=False)

   # Group actions
   def renameGroup(self, nameorid, newname):
      print("Rename group <%s> to <%s>" %(nameorid, newname))
      
   def addGroup(self, name):
      print("Add group <%s>" %(name))
      
   def deleteGroup(self, nameorid):
      print("Delete group <%s>" %(nameorid))

   def muteGroups(self, nameorids=None, mute=False):

      # Group name or id string
      if(type(nameorids) is str):
         nameorids = [nameorids]

      # Empty list implies all groups
      if(len(nameorids)==0):
         nameorids = map(lambda g: g.identifier , self._snapserver.groups)

      for gid in nameorids:
         group = self._groupByNameOrId(gid)
         obj = group.set_muted(mute)
         self._loop.run_until_complete(obj)
         if(self._verbose):
            print("Mute %s status %s" %(group.friendly_name, mute))

   #
   # Lookup functions
   #
   def _groupByNameOrId(self, nameorid):
      try:
         return self._snapserver.group(nameorid)

      except KeyError:
         for g in self._snapserver.groups:
            if(g.name == nameorid):
               return g

         raise
      
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
   subparsers = parser.add_subparsers(help='Snapcast control commands')
   
   #
   # The group command
   #
   parser_group = subparsers.add_parser('group', help='Group commands')
   group_sub = parser_group.add_subparsers()

   # snapctl group mute
   parser_group_mute = group_sub.add_parser('mute', help='Mute a group volume')
   parser_group_mute.set_defaults(mutegroup=True)
   parser_group_mute.add_argument('nameorid', nargs='*', help='Name or id of group(s)')

   # snapctl group unmute
   parser_group_unmute = group_sub.add_parser('unmute', help='Unmute a group volume')
   parser_group_unmute.set_defaults(unmutegroup=True)
   parser_group_unmute.add_argument('nameorid', nargs='*', help='Name or id of group(s)')

   # snapctl group volume <percent>
   parser_group_volume = group_sub.add_parser('volume', help='Set a group volume')
   parser_group_volume.set_defaults(volumegroup=True)
   parser_group_volume.add_argument('percent', action='store', help='Group volume')
   parser_group_volume.add_argument('nameorid', nargs='*', help='Name or id of group(s)')

   # snapctl group show <nameorid>
   parser_group_show = group_sub.add_parser('show', help='Display information about one,more or all groups')
   parser_group_show.set_defaults(showgroup=True)
   parser_group_show.add_argument('nameorid', nargs='*', help='Name or id of group(s)')

   # snapctl group add <name> 
   parser_group_add = group_sub.add_parser('add', help='Add a new group')
   parser_group_add.set_defaults(addgroup=True)
   parser_group_add.add_argument('newname', action='store', help='New group name')

   # snapctl group del <nameorid> 
   parser_group_del = group_sub.add_parser('delete', help='Delete a group')
   parser_group_del.set_defaults(delgroup=True)
   parser_group_del.add_argument('nameorid', action='store', help='Group to delete')

   # snapctl group rename <nameorid> <name>
   parser_group_ren = group_sub.add_parser('rename', help='Rename a group')
   parser_group_ren.set_defaults(rengroup=True)
   parser_group_ren.add_argument('nameorid', action='store', help='Group to rename')
   parser_group_ren.add_argument('newname', action='store', help='New group name')

   #
   # The stream command
   #
   parser_stream = subparsers.add_parser('stream', help='Stream commands')
   stream_sub = parser_stream.add_subparsers()

   # snapctl stream show <nameorid>
   parser_stream_show = stream_sub.add_parser('show', help='Show one or all streams')
   parser_stream_show.add_argument('-m', '--meta', action='store_true', default=False, help='Display metadata')
   parser_stream_show.set_defaults(showstream=True)
   parser_stream_show.add_argument('nameorid',nargs='*')

   #
   # The client command
   #
   parser_client = subparsers.add_parser('client', help='Client commands')
   client_sub = parser_client.add_subparsers()

   # snapctl client show <nameorid>
   parser_client_show = client_sub.add_parser('show', help='Show a client')
   parser_client_show.set_defaults(showclient=True)
   parser_client_show.add_argument('nameorid',nargs='*')

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

   # Show one or more clients
   elif('showclient' in args and args.showclient):
      if args.nameorid:
         for nameorid in args.nameorid:
            controller.showClient(nameorid)
      else:
         controller.showAllClients()

   # Add a group
   elif('addgroup' in args and args.addgroup):
      controller.addGroup(args.newname)

   # Delete a group
   elif('delgroup' in args and args.delgroup):
      controller.deleteGroup(args.nameorid)

   # Rename a group
   elif('rengroup' in args and args.rengroup):
      controller.renameGroup(args.nameorid, args.newname)

   # Mute a group
   elif('mutegroup' in args and args.mutegroup):
      controller.muteGroups(args.nameorid, mute=True)

   # Unmute a group
   elif('unmutegroup' in args and args.unmutegroup):
      controller.muteGroups(args.nameorid, mute=False)

   # Set group volume
   elif('volumegroup' in args and args.volumegroup):
      print("Set group volume")

   # No arguments given, display help
   else:
      parser.print_help()

if __name__ == '__main__':
   main()

