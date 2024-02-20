#!/bin/bash
# entrypoint.sh

echo "Building the sender image..."
docker build /app/medidor -t medidor:latest

echo "Image built. Proceeding with the original command..."
exec "$@"
