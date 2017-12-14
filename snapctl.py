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

def getdefault(a,b):
   if a:
      return a
   return b

def gettag(meta, tag, default):
   if tag in meta:
      return meta[tag]
   return default

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
         artist = gettag(meta, 'ARTIST', '-unknown-')
         album = gettag(meta, 'ALBUM', '-unknown-')
         title = gettag(meta, 'TITLE', '-unknown-')

      if multiline or self._verbose:
         print('Stream ID  : %s' %(stream.identifier))
         print('   name    : %s' %(stream.name))
         if meta and stream.status != 'idle':
            print('   Artist  : %s' %(artist))
            print('   Album   : %s' %(album))
            print('   Title   : %s' %(title))
         print()

      else:
         if meta and stream.status != 'idle':
            print("%s playing '%s' by %s" %(stream.name, title, artist))
         else:  
            print('[%s] %s' %(stream.state, stream.name))

   def showAllStreams(self, meta=False):
      for stream in self._snapserver.streams:
         self.showStream(stream, meta=meta, multiline=False)

   # Client information
   def showClient(self, client, multiline=True):
      if(type(client) is str):
         client = self._clientByNameOrId(client)

      clientname = getdefault(client.name, '-noname-')
      groupname = getdefault(client.group.name, '-noname-')

      if multiline or self._verbose:
         print('Client ID  : %s' %(client.identifier))
         print('   name    : %s' %(clientname))
         print('   host    : %s' %(client.hostname))
         print('   group   : %s' %(groupname))
         print('   muted   : %s' %(client.muted))
         print('   online  : %s' %(client.connected))
         print()

      elif client.connected:
         print('%s (%s)' %(clientname, groupname))

   def showAllClients(self):
      for client in self._snapserver.clients:
         self.showClient(client, multiline=False)

   def moveClient(self, nameorid, groupnameorid):
      pass

   def renameClient(self, nameorid, newname):
      client = self._clientByNameOrId(nameorid)
      obj = client.set_name(newname)
      self._loop.run_until_complete(obj)

   def muteClients(self, nameorids, mute=True):
      nameorids = self._expandClients(nameorids)
      for cid in nameorids:
         client = self._snapserver.client(cid)
         obj = client.set_muted(mute)
         self._loop.run_until_complete(obj)
         if(self._verbose):
            print("Mute '%s' status %s" %(client.name, mute))

   # Group information
   def showGroup(self, group, multiline=True, meta=False):
      if(type(group) is str):
         group = self._groupByNameOrId(group)

      groupname = getdefault(group.name, '-noname-')
      streamname = getdefault(group.stream, '-none-')
  
      has_meta = meta
      stream = self._snapserver.stream(group.stream)

      if meta and stream.status != 'idle':
         artist = gettag(stream.meta, 'ARTIST', '-unknown-')
         album = gettag(stream.meta, 'ALBUM', '-unknown-')
         title = gettag(stream.meta, 'TITLE', '-unknown-')
         has_meta = True

      if multiline or self._verbose:
         print('Group ID   : %s' %(group.identifier))
         print('   name    : %s' %(group.name))
         print('   muted   : %s' %(group.muted))
         print('   stream  : %s' %(group.stream))

         if has_meta:
            print()
            print('   Stream tags:')
            print('      Artist  : %s' %(artist))
            print('      Album   : %s' %(album))
            print('      Title   : %s' %(title))

         print()
         print('   clients :')
         for cid in group.clients:
            client = self._snapserver.client(cid)
            clientname = getdefault(client.name, client.identifier)
            print('      %s' %(clientname))
         print()

      else:
         is_muted = ''
         if group.muted:
            is_muted = ' (muted)'

         print('[%s] %s%s, stream %s' %(group.identifier, groupname, is_muted, streamname))

   def showAllGroups(self, meta=False):
      for group in self._snapserver.groups:
         self.showGroup(group, multiline=False, meta=meta)

   # Group actions
   def assignStream(self, nameorid, stream):
      group = self._groupByNameOrId(nameorid)
      obj = group.set_stream(stream)
      self._loop.run_until_complete(obj)

   def renameGroup(self, nameorid, newname):
      print("Rename group <%s> to <%s>" %(nameorid, newname))
      group = self._groupByNameOrId(nameorid)
      obj = group.rename(newname)
      self._loop.run_until_complete(obj)
      
   def addGroup(self, name):
      print("Add group <%s>" %(name))
      obj = self._snapserver.group_add(name)
      self._loop.run_until_complete(obj)
      
   def deleteGroup(self, nameorid):
      print("Delete group <%s>" %(nameorid))
      group = self._groupByNameOrId(nameorid)
      obj = group.delete()
      self._loop.run_until_complete(obj)

   def setGroupVolume(self, percent, nameorid):
      nameorids = self._expandGroups(nameorids)
      for gid in nameorids:
         group = self._groupByNameOrId(gid)
         obj = group.set_volume(volume)
         self._loop.run_until_complete(obj)
         if(self._verbose):
            print("Volume for %s set to %s%%" %(group.name, volume))

   def muteGroups(self, nameorids=None, mute=False):
      nameorids = self._expandGroups(nameorids)
      for gid in nameorids:
         group = self._groupByNameOrId(gid)
         obj = group.set_muted(mute)
         self._loop.run_until_complete(obj)
         if(self._verbose):
            print("Mute %s status %s" %(group.name, mute))

   #
   # Lookup functions
   #
   def _clientByNameOrId(self, nameorid):
      try:
         return self._snapserver.client(nameorid)

      except KeyError:
         for c in self._snapserver.clients:
            if(c.name == nameorid):
               return c

         raise

   def _groupByNameOrId(self, nameorid):
      try:
         return self._snapserver.group(nameorid)

      except KeyError:
         for g in self._snapserver.groups:
            if(g.name == nameorid):
               return g

         raise

   def _expandClients(self, nameorids):

      # Client name or id string
      if(type(nameorids) is str):
         nameorids = [nameorids]

      # Empty list implies all clients
      if(len(nameorids)==0):
         nameorids = map(lambda g: g.identifier , self._snapserver.clients)

      return nameorids

   def _expandGroups(self, nameorids):

      # Group name or id string
      if(type(nameorids) is str):
         nameorids = [nameorids]

      # Empty list implies all groups
      if(len(nameorids)==0):
         nameorids = map(lambda g: g.identifier , self._snapserver.groups)

      return nameorids

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
   parser.add_argument('-m', '--meta', action='store_true', default=False, help='Display metadata where applicable')
   parser.add_argument('-s', '--server', default=os.environ.get('SNAPSERVER', '127.0.0.1:1705'))
   subparsers = parser.add_subparsers(help='Snapcast control commands')
   
   #
   # The group command
   #
   parser_group = subparsers.add_parser('group', help='Group commands')
   group_sub = parser_group.add_subparsers()

   # snapctl group stream <nameorid> <id>
   parser_group_stream = group_sub.add_parser('stream', help='Mute a group volume')
   parser_group_stream.set_defaults(assigngroup=True)
   parser_group_stream.add_argument('nameorid', help='Name or id of group')
   parser_group_stream.add_argument('stream', help='Stream to assign')

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
   parser_client_ren.add_argument('nameorid', action='store', help='Client to rename')
   parser_client_ren.add_argument('newname', action='store', help='New client name')

   # snapctl client move <nameorid> <group nameorid>
   parser_client_move = client_sub.add_parser('move', help='Rename a client')
   parser_client_move.set_defaults(moveclient=True)
   parser_client_move.add_argument('groupnameorid', help='Name or id of target group')
   parser_client_move.add_argument('nameorid', nargs='*', help='Name or id of client(s)')

   # snapctl client mute
   parser_client_mute = client_sub.add_parser('mute', help='Mute a client volume')
   parser_client_mute.set_defaults(muteclient=True)
   parser_client_mute.add_argument('nameorid', nargs='*', help='Name or id of client(s)')

   # snapctl client unmute
   parser_client_unmute = client_sub.add_parser('unmute', help='Unmute a client volume')
   parser_client_unmute.set_defaults(unmuteclient=True)
   parser_client_unmute.add_argument('nameorid', nargs='*', help='Name or id of client(s)')

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

   # Show one or more clients
   elif('showclient' in args and args.showclient):
      if args.nameorid:
         for nameorid in args.nameorid:
            controller.showClient(nameorid)
      else:
         controller.showAllClients()

   # Rename a client
   elif('renclient' in args and args.renclient):
      controller.renameClient(args.nameorid, args.newname)

   # Assign a client to a target group
   elif('moveclient' in args and args.moveclient):
      controller.moveClient(args.nameorid, args.groupnameorid)

   # Mute a client
   elif('muteclient' in args and args.muteclient):
      controller.muteClients(args.nameorid, mute=True)

   # Unmute a client
   elif('unmuteclient' in args and args.unmuteclient):
      controller.muteClients(args.nameorid, mute=False)

   # Show one or more groups
   elif('showgroup' in args and args.showgroup):
      if args.nameorid:
         for nameorid in args.nameorid:
            controller.showGroup(nameorid, meta=args.meta)
      else:
         controller.showAllGroups(meta=args.meta)

   # Add a group
   elif('addgroup' in args and args.addgroup):
      controller.addGroup(args.newname)

   # Delete a group
   elif('delgroup' in args and args.delgroup):
      controller.deleteGroup(args.nameorid)

   # Rename a group
   elif('rengroup' in args and args.rengroup):
      controller.renameGroup(args.nameorid, args.newname)

   # Assign a stream to a group
   elif('assigngroup' in args and args.assigngroup):
      controller.assignStream(args.nameorid, args.stream)

   # Mute a group
   elif('mutegroup' in args and args.mutegroup):
      controller.muteGroups(args.nameorid, mute=True)

   # Unmute a group
   elif('unmutegroup' in args and args.unmutegroup):
      controller.muteGroups(args.nameorid, mute=False)

   # Set group volume
   elif('volumegroup' in args and args.volumegroup):
      controller.setGroupVolume(args.percent, args.nameorid)

   # No arguments given, display help
   else:
      parser.print_help()

if __name__ == '__main__':
   main()

