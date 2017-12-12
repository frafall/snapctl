Snapctl - snapcast control

I discovered [python-snapcast](https://github.com/happyleavesaoc/python-snapcast) and discarded
my feeble attempts on doing the same.

Now I can focus on what I really wanted.. :)

So, now on to Home Assistant.

I would like a media_player that:
- displays one zone which I can select interactively or by config
- displays metadata for the associated stream if available
- enables volume/mute for zone
- select stream played in zone

I also need a configuration interface for snapcast, ie select which 
speakers are in which zone, something like a list of speakers and
a selection list of zones, perhaps a mute button for speaker

But damn, I need snapcast to hardcode zones to be practical
So, while looking into a hass module I have to see how to 
make static groups/zones in snapcast
