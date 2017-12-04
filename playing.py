#!/usr/bin/python3
import sys
import logging
import snapcast.control
import asyncio
import json

#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
#logger = logging.getLogger(__name__)

ioloop = asyncio.get_event_loop()

def run_test(loop):
        return (yield from snapcast.control.create_server(loop, 'gandalf'))

snapserver = ioloop.run_until_complete(run_test(ioloop))

def tag(jtag, name, default=None):
	if(name in jtag):
		return jtag[name]
	return default

for group in snapserver.groups:
	stream = snapserver.stream(group.stream)

	if(stream.status != 'idle'):
		jtag   = stream._stream.get('meta')
		title = tag(jtag, 'TITLE')
		artist = tag(jtag, 'ARTIST')
		if(title): 
			state = 'playing "%s" by %s from stream <%s>' %(title, artist, stream.friendly_name)
		else:
			state = '-idle-'
		print("Zone: %s" %(group.friendly_name))
		print("\t stream: %s" %(stream.friendly_name))
		print("\t artist: %s" %(artist))
		print("\t  title: %s" %(title))

		for client_id in group.clients:
			client = snapserver.client(client_id)
			print("\tspeaker: %s" %(client.friendly_name))
