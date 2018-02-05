---
layout: base
---

# Broca

This is a proxy server that translates [Synapse](https://synapse-bt.org) RPC
into [Transmission](https://transmissionbt.com/) RPC.

To use it, run the daemon and point your Transmission client at it. Set the
username to your desired Synapse RPC URI (e.g. ws://localhost:8412) and the
password to your Synapse RPC password, and the host to http://localhost:9091.

## Transmission clients known to work

- transmission-remote-gtk
- transgui
- Gear Shift
- tremc
- Transdroid

## Releases

Broca is under development and releases are not currently available.

## Development

Broca development is organized on
[GitHub](https://github.com/SirCmpwn/broca). To contribute, send pull
requests. To report bugs, open GitHub issues.
