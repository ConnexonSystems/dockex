#!/bin/bash

cd "${0%/*}"
cd ..

# if bootstrap container exists kill/remove it
if [[ "$(docker ps -a -q -f name=dockex_bootstrap)" ]]; then
    docker rm -f dockex_bootstrap
fi

# build bootstrap image and run container
docker build -f dockex_bootstrap/Dockerfile --tag=dockex_bootstrap_image . && \
    docker run -it -v /var/run/docker.sock:/var/run/docker.sock --name dockex_bootstrap dockex_bootstrap_image
