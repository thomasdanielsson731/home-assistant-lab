ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base:3.20
FROM ${BUILD_FROM}

ARG BUILD_VERSION=0.2.7
ARG BUILD_ARCH

RUN apk add --no-cache python3 py3-pip \
    && pip3 install --no-cache-dir --break-system-packages \
        requests paho-mqtt python-dotenv websocket-client

COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
