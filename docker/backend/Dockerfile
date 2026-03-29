# SPDX-License-Identifier: MIT



FROM golang:1.23-bullseye AS golang-builder

# Write final binaries to / so it's easy to copy them out
ENV GOBIN=/
# Disable CGO to ensure the binaries are statically linked
# Discussion: https://github.com/chaoss/augur/pull/3142
ENV CGO_ENABLED=0

RUN go install github.com/boyter/scc/v3@v3.4.0 \
    && /scc --version
RUN go install github.com/ossf/scorecard/v5@v5.1.1 \
    && /scorecard version


########################################
FROM python:3.11-slim-bullseye

LABEL maintainer="outdoors@acm.org"

ARG VERSION
LABEL version=${VERSION}

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/usr/bin/:/usr/local/bin:/usr/lib:${PATH}"

RUN set -x \
    && apt-get update \
    && apt-get -y install --no-install-recommends \
        git \
        bash \
        curl \
        gcc \
        software-properties-common \
        postgresql-contrib \
        musl-dev \
        wget \
        postgresql-client \
        libpq-dev \
        build-essential \
        tar \
        jq \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

EXPOSE 5000

# Install uv (https://docs.astral.sh/uv/guides/integration/docker/#installing-uv)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1
# The uv package cache will be on a cache volume, so can't be linked
ENV UV_LINK_MODE=copy
# Assert that the lockfile (uv.lock) is up-to-date. Use `uv lock` to update it
# manually if this fails the container build.
ENV UV_LOCKED=1

WORKDIR /augur

COPY pyproject.toml .
COPY uv.lock .
COPY .python-version .

# Install augur's dependencies early to take advantage of build cache
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

# Copy in the actual code
# The RUN line below ensure that permissions are set correctly.
# This is the equivalent of the following docker --chmod flags, but done in a way thats compatible with podman.
# This can be removed once https://github.com/containers/buildah/issues/6066 or relevant equivalent is fixed
# - u=rw,u+X: user can read and write all files/dirs and execute directories
# - go=r,go+X: group and others can read all files/dirs and execute directories
COPY README.md .
COPY LICENSE .
COPY alembic.ini .
COPY augur/ augur/
COPY metadata.py .
COPY scripts/ scripts/
COPY keyman/ keyman/

RUN find augur -type d -exec chmod u=rwx,go=rx {} + && find augur -type f -exec chmod u=rw,go=r {} +
RUN find keyman -type d -exec chmod u=rwx,go=rx {} + && find keyman -type f -exec chmod u=rw,go=r {} +
RUN find scripts -exec chmod u=rwx,go=rx {} +


# Install the main project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-dev

# We aren't going to activate the virtualenv (manually or via uv run), so we
# need adjust the PATH
ENV PATH="/augur/.venv/bin:${PATH}"

ENV SCC_DIR=/scc
COPY --from=golang-builder --chmod=755 "/scc" "/scc/scc"
ENV SCORECARD_DIR=/scorecard
COPY --from=golang-builder --chmod=755 "/scorecard" "/scorecard/scorecard"
# Verify installations
RUN ${SCC_DIR}/scc --version
RUN ${SCORECARD_DIR}/scorecard version

RUN mkdir -p repos/ logs/ /augur/facade/
RUN ln -s /cache /augur/augur/static/cache

# Copy in the entrypoint and init scripts, ensuring they are executable
COPY --chmod=755 ./docker/backend/entrypoint.sh /
COPY --chmod=755 ./docker/backend/init.sh /
RUN chmod +x /entrypoint.sh /init.sh
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
CMD ["/init.sh"]
