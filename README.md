Snapctl - snapcast control

Work in progress....

A simple python interface to Snapcast control, built
in preparation of a Home Assistant control interface.

```sh
snapctl dump
snapctl list clients
snapctl list streams
snapctl list groups
snapctl info <object name or id>

Todo:
snapctl mute <client>
snapctl volume <client> +- db/%
snapctl move <client> to <stream>

snapctl info client
snapctl info stream
```

Notes:
I use the Python v3 'queue', to use in Python v2 you need to install 'future' package.

** Home Assistant **
I would like to:
1. Have a 'media_player' per zone, showing meta information for media played in zone 
   NB! missing meta data in snapcast for this.
2. Select stream input for zone 
3. Volume/mute zone
4. Move clients between zones (rarely done)

TODO
----
- [ ] **Change** Move signal handling into SnapServer class
