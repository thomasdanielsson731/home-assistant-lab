ARG BUILD_FROM
FROM $BUILD_FROM

# Scaffold — Python + repo scripts synced to /share/danielsson-insights/
RUN apk add --no-cache python3 py3-pip \
    && pip3 install --no-cache-dir --break-system-packages \
        python-dotenv requests paho-mqtt

COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
