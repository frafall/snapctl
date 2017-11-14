#!/usr/bin/python
import os
import argparse
import telnetlib
import json
import time

"""
   Snapcast control utility

   Use cases:

      snapctl list clients
      snapctl list streams
      snapctl mute <client>
      snapctl volume <client> +- db/%

      snapctl move <client> to <stream>

      snapctl info client
      snapctl info stream

      snapctl dump				# Dump raw JSON return

   Streams/clients has ID's but not intuitive, use name mapping?

   Prerequisite:
      pip install zeroconf (TBD)
"""

class SnapServer(object):
   """
   Representation of a Snapcast server
   """
   reqId = 1

   def __init__(self, hostname):
      """If no hostname given, read SNAPSERVER from environment or fall back to localhost."""
      self.connection = telnetlib.Telnet(hostname, 1705)

   def doRequest(self, j, requestId):
      #print("send: " + j)
      self.connection.write(j + "\r\n")
      while (True):
         response = self.connection.read_until("\r\n", 2)
         jResponse = json.loads(response)
         if 'id' in jResponse:
            if jResponse['id'] == requestId:
               #print("recv: " + response)
               return jResponse
      return

   def cmdGetStatus(self):
      return self.doRequest(json.dumps({'jsonrpc': '2.0', 'method': 'Server.GetStatus', 'id': 1}), 1)

#
# Main command line 
#
def main():
   parser = argparse.ArgumentParser()
   parser.add_argument('-v', '--verbose', action='count')
   parser.add_argument('-d', '--debug', action='store_true')
   parser.add_argument('-s', '--server', default=os.environ.get('SNAPSERVER', '127.0.0.1')) 
   sub = parser.add_subparsers()

   # The dump command
   parser_dump = sub.add_parser('dump')
   parser_dump.set_defaults(dump=True)

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
   srv = SnapServer(args.server)

   # Do the dump command
   if(getattr(args, 'dump', False)):
      result = srv.cmdGetStatus()
      print json.dumps(result, indent=3, sort_keys=True)

   # List the clients
   elif(getattr(args, 'listclients', False)):
      result = srv.cmdGetStatus()
      for group in result["result"]["server"]["groups"]:
         for entry in group["clients"]:
            if(args.verbose):
               print("%-20s\t%s [%d]" %(entry["config"]["name"], entry["host"]["mac"], entry["config"]["instance"]))
            else:
               print("%-20s" %(entry["config"]["name"]))

   # List the streams
   elif(getattr(args, 'liststreams', False)):
      result = srv.cmdGetStatus()
      for entry in result["result"]["server"]["streams"]:
         details = ""
         if(args.verbose):
            details = entry["uri"]["raw"]
         print("%-20s %s\t%s" %(entry["id"], entry["status"], details))

   # List the groups
   elif(getattr(args, 'listgroups', False)):
      result = srv.cmdGetStatus()
      for entry in result["result"]["server"]["groups"]:
         if(entry["name"]):
            name = entry["name"]
         else:
            name = entry["stream_id"]

         if(args.verbose):
            print("%-20s\t%s\t%s" %(name, entry["stream_id"], entry["id"]))
         else:
            print("%-20s\t%s" %(name, entry["stream_id"]))

         if(args.verbose):
            for client in entry["clients"]:
               print("   %s" %(client["config"]["name"]))
            print("")

if __name__ == '__main__':
   main()

