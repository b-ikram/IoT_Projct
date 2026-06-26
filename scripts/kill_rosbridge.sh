#!/bin/bash
echo "Stopping rosbridge only..."

pkill -f rosbridge_websocket
pkill -f rosbridge_server
pkill -f rosapi_node
pkill -f rosapi

sudo fuser -k 9090/tcp 2>/dev/null

echo "Rosbridge stopped."
