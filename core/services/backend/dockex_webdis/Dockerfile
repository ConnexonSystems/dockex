FROM alpine

RUN apk -U upgrade && \
    apk add alpine-sdk libevent libevent-dev bsd-compat-headers git && \
    git clone --depth 1 https://github.com/nicolasff/webdis.git /tmp/webdis && \
    cd /tmp/webdis && \
    make clean all && \
    cp webdis /usr/local/bin/ && \
    cp webdis.json /etc/ && \
    mkdir -p /usr/share/doc/webdis && \
    cp README.markdown /usr/share/doc/webdis/README && \
    cd /tmp && \
    rm -rf /tmp/webdis && \
    apk del --purge alpine-sdk libevent-dev bsd-compat-headers git && \
    rm -rf /var/cache/apk/*

CMD ["webdis", "/tmp/dockex/webdis.json"]
