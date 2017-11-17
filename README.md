Snapctl - snapcast control

Work in progress....

A simple python interface to Snapcast control, built
in preparation of a Home Assistant control interface.

```sh
snapctl list clients
snapctl list streams
snapctl mute <client>
snapctl volume <client> +- db/%

snapctl move <client> to <stream>

snapctl info client
snapctl info stream

snapctl dump
```

Notes:
I use the Python v3 'queue', to use in Python v2 you need to install 'future' package.


TODO
----
- [ ] **Change** Move signal handling into SnapServer class
