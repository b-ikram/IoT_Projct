#!/bin/bash

echo "Checking rosbridge..."

if sudo lsof -i :9090 >/dev/null 2>&1; then
 echo " Rosbridge is running on port 9090"
 sudo lsof -i :9090
else
 echo " Rosbridge is NOT running on port 9090"
fi
