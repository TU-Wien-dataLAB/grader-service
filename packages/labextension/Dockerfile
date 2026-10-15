ARG REGISTRY=quay.io
ARG OWNER=jupyter
ARG BASE_CONTAINER=$REGISTRY/$OWNER/minimal-notebook:latest

FROM $BASE_CONTAINER AS builder

USER root

# Set this for mamba (it uses pip internally) and pip
ENV PIP_CACHE_DIR=/root/.cache/pip

# Install build dependencies only
RUN apt-get update && \
    apt-get install -yq --no-install-recommends \
        git \
        build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Node is only needed to build the labextension
RUN --mount=type=cache,target=/opt/conda/pkgs \
    mamba install -y nodejs && \
    mamba clean -a -y

WORKDIR /build

# Copy only what is needed to build
COPY . /build

# Build and install the labextension
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --root-user-action=ignore /build && rm -rf /build

WORKDIR /home/jovyan
USER jovyan
