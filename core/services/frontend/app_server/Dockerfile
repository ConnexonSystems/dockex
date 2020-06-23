FROM node:10

WORKDIR /dockex

COPY app/package.json /dockex/app/package.json
RUN cd /dockex/app && yarn install

COPY app /dockex/app
COPY core/services/frontend/app_server/launch_app_server.sh /dockex/

ENTRYPOINT ["bash", "/dockex/launch_app_server.sh"]
