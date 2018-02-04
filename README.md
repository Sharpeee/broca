# Broca

This is a proxy server that translates [Synapse](https://synapse-bt.org) RPC
into [Transmission](https://transmissionbt.com/) RPC.

To use it, run the daemon and point your Transmission client at it. Set the
username to your desired Synapse RPC URI (e.g. ws://localhost:8412) and the
password to your Synapse RPC password, and the host to http://localhost:9091.
