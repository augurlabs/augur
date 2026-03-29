FROM rabbitmq:4.1-management-alpine

LABEL maintainer="574/augur@simplelogin.com"

ARG VERSION
LABEL version=${VERSION}

ARG RABBIT_MQ_DEFAULT_USER=augur
ARG RABBIT_MQ_DEFAULT_PASSWORD=password123
ARG RABBIT_MQ_DEFAULT_VHOST=augur_vhost

COPY --chown=rabbitmq:rabbitmq ./docker/rabbitmq/augur.conf /etc/rabbitmq/conf.d/

ADD docker/rabbitmq/definitions.json /etc/rabbitmq/

ADD docker/rabbitmq/advanced.config /etc/rabbitmq/
RUN chown rabbitmq:rabbitmq /etc/rabbitmq/advanced.config

RUN chmod 777 /etc/rabbitmq/conf.d/augur.conf

RUN apk add --no-cache python3
COPY docker/rabbitmq/update_config.py /

RUN exec python3 update_config.py

RUN chown rabbitmq:rabbitmq /etc/rabbitmq/definitions.json
