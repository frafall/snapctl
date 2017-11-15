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

