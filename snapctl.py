#!/usr/bin/python
import os, socket
import argparse
import json
import snapcast

"""
   Snapcast control utility

   Author: frafall

   Use cases:

      # List objects
      snapctl list clients
      snapctl list streams
      snapctl list groups

      # Control functions
      snapctl mute <client> or <group>
      snapctl volume <client> or <group> +- db/%
      snapctl move <client> to <group>
      snapctl move <group> to <stream>

      # Show information about objects
      snapctl info group  <id>
      snapctl info client <id>
      snapctl info stream <id>

      # Events ?
      snapctl monitor

      # Raw JSON output
      snapctl dump

   JSON API:
      Client.GetStatus
      Client.SetVolume		notifications
      Client.SetLatency		notifications
      Client.SetName		notifications

      Group.GetStatus
      Group.SetMute		notifications
      Group.SetStream		notifications
      Group.SetClients		returns server status, notifications
      
      Server.GetRPCVersion
      Server.GetStatus		returns server status
      Server.DeleteClient	returns server status, notifications


   Streams/clients has ID's but not intuitive, use name mapping?

   Prerequisite:
      pip install zeroconf (TBD)
"""

def DumpObject(srv, objectid):
   result = srv.GetStatus()

   for group in result["result"]["server"]["groups"]:
      for entry in group["clients"]:
         if(entry['id'] == objectid or entry['host']['mac'] == objectid or objectid in entry['config']['name']):
            print 'Client: ' + json.dumps(entry, indent=3, sort_keys=True)
            return

   for entry in result["result"]["server"]["streams"]:
      if(entry['id'] == objectid):
         print 'Stream: ' + json.dumps(entry, indent=3, sort_keys=True)
         return

   for entry in result["result"]["server"]["groups"]:
      if(entry['id'] == objectid):
         print 'Group: ' + json.dumps(entry, indent=3, sort_keys=True)
         return

#
# Main command line 
#
def main():
   parser = argparse.ArgumentParser()
   parser.add_argument('-v', '--verbose', action='count')
   parser.add_argument('-d', '--debug', action='store_true')
   parser.add_argument('-s', '--server', default=os.environ.get('SNAPSERVER', '127.0.0.1')) 
   sub = parser.add_subparsers()

   # The info command
   parser_info = sub.add_parser('info')
   parser_info.set_defaults(info=True)
   parser_info.add_argument('objectid', nargs=1)

   #ssub = parser_info.add_subparsers()
   #info_client = ssub.add_parser('client')
   #info_client.add_argument('objectid', nargs=1)

   # The dump command
   parser_dump = sub.add_parser('dump')
   parser_dump.set_defaults(dump=True)

   # The monitor command
   parser_monitor = sub.add_parser('monitor')
   parser_monitor.set_defaults(monitor=True)

   # The list command
   parser_list = sub.add_parser('list')
   ssub = parser_list.add_subparsers()

   # Subparser to select what to list
   parser_list_clients = ssub.add_parser('clients')
   parser_list_clients.set_defaults(listclients=True)
   parser_list_streams = ssub.add_parser('streams')
   parser_list_streams.set_defaults(liststreams=True)
   parser_list_groups = ssub.add_parser('groups')
   parser_list_groups.set_defaults(listgroups=True)

   # Parse it
   args = parser.parse_args()

   # If no server given look service '_snapcast-jsonrpc._tcp' up in mdns
   try:
      srv = snapcast.SnapServer(args.server, debug=args.debug)
   except socket.error as detail:
      print('Connection to %s refused!' %(args.server))
      return 

   # Do the dump command
   if(getattr(args, 'dump', False)):
      result = srv.GetStatus()
      print json.dumps(result, indent=3, sort_keys=True)

   # List the clients
   elif(getattr(args, 'listclients', False)):
      result = srv.GetStatus()
      for group in result["result"]["server"]["groups"]:
         for entry in group["clients"]:
            if(args.verbose):
               print("%-20s\t%s [%d]" %(entry["config"]["name"], entry["host"]["mac"], entry["config"]["instance"]))
            else:
               print("%-20s" %(entry["config"]["name"]))

   # List the streams
   elif(getattr(args, 'liststreams', False)):
      result = srv.GetStatus()
      for entry in result["result"]["server"]["streams"]:
         details = ""
         if(args.verbose):
            details = entry["uri"]["raw"]
         print("%-20s %s\t%s" %(entry["id"], entry["status"], details))

   # List the groups
   elif(getattr(args, 'listgroups', False)):
      result = srv.GetStatus()
      for group in result["result"]["server"]["groups"]:
         label = group['stream_id']
         if 'name' in group and group['name']:
            label = group['name']
         details = ""
         if(args.verbose):
            details = group["id"]
         print("%-20s\t%s" %(label, details))
         if(args.verbose):
            for client in group["clients"]:
               print("   %-20s" %(client["config"]["name"]))

   # Info/details on objects
   elif(getattr(args, 'info', False)):
      DumpObject(srv, args.objectid[0])

   # Monitor the Snapcast server
   elif(getattr(args, 'monitor', False)):
      print("Monitor")

   # Close down connection again
   srv.close()


if __name__ == '__main__':
   main()

