FROM python:3.11.12-alpine

LABEL maintainer="outdoors@acm.org"

ARG VERSION
LABEL version=${VERSION}

RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir redis==4.3.3

ENV KEYMAN_DOCKER=1
ENV PYTHONPATH="${PYTHONPATH}:/augur"
# Ensure Python output is sent straight to terminal (e.g. for Docker logs)
ENV PYTHONUMBUFFERED=1

WORKDIR /augur
COPY ./keyman keyman/
RUN find . -type d -exec chmod u=rwx,go=rx {} + && find . -type f -exec chmod u=rw,go=r {} +


ENTRYPOINT [ "python", "/augur/keyman/Orchestrator.py" ]
