#!/bin/bash
set -e

# Check if the Docker socket exists
if [ -S /var/run/docker.sock ]; then
    # Run your Python autoscaler script with Docker socket mounted
    exec python autoscaler.py "$@"
else
    echo "Error: Docker socket not found"
    exit 1
fi