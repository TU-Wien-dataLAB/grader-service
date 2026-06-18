ARG REGISTRY=quay.io
ARG OWNER=jupyter
ARG BASE_CONTAINER=$REGISTRY/$OWNER/minimal-notebook:latest

FROM $BASE_CONTAINER AS builder

USER root

# Install build dependencies only
RUN apt-get update && \
    apt-get install -yq --no-install-recommends \
        git \
        build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Node is only needed to build the labextension
RUN mamba install -y nodejs && \
    mamba clean -a -y

WORKDIR /build

# Copy only what is needed to build
COPY . /build

# Build and install the labextension
RUN pip install /build && rm -rf /build

WORKDIR /home/jovyan
USER jovyan
