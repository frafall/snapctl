Snapctl - snapcast control

I discovered [python-snapcast](https://github.com/happyleavesaoc/python-snapcast) and discarded
my feeble attempts on doing the same.

Now I can focus on what I really wanted.. :)

First test is to verify the metadata interface - and it works with unmodified
python-snapcast, check playing.py

So, now on to Home Assistant.

I would like a media_player that:
- displays one group which I can select interactively or by config
- displays metadata for the associated stream if available
- enables volume/mute for group

I also need a configuration interface for snapcast, ie select which 
speakers are in which zone, something like a list of speakers and
a selection list of zones

But damn, I need snapcast to hardcode zones to be practical

