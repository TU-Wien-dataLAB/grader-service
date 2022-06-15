# Copyright (c) 2022, TU Wien
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

ARG BASE_IMAGE=ubuntu:focal
FROM ${BASE_IMAGE} as builder

ENV GRADER_SERVICE_HOST="0.0.0.0"
ENV GRADER_HOST_URL="0.0.0.0"
ENV GRADER_SERVICE_DIRECTORY="/var/lib/grader-service"
ENV GRADER_HOST_URL="0.0.0.0"
ENV GRADER_DB_DIALECT="sqlite"
ENV GRADER_DB_HOST="/var/lib/grader-service/grader.db"
ENV GRADER_AUTOGRADE_IN_PATH="/var/lib/grader-service/convert_in"
ENV GRADER_AUTOGRADE_OUT_PATH="/var/lib/grader-service/convert_out"

# Create grader-service user
RUN groupadd -g 1000 grader-service && \
    useradd -m -d /var/lib/grader-service -s /bin/nologin -u 1000 -g 1000 grader-service

RUN apt-get update \
    && apt-get install -yq --no-install-recommends \
    python3 \
    python3-pip \
    git \
    vim \
    iputils-ping \
    tini && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# INSTALL grader-service
COPY ./grader_service /grader_service
COPY ./grader_convert /grader_convert
COPY ./grader_service.sh /usr/local/bin/grader_service.sh
# install dependencies
RUN python3 -m pip install -r /grader_convert/requirements.txt && \
    python3 -m pip install -r /grader_service/requirements.txt

RUN python3 -m pip install --no-use-pep517 /grader_convert/ && \
    python3 -m pip install --no-use-pep517 /grader_service/ 
    # && \
    # rm -rf /convert/ && \
    # rm -rf /grader_service/

USER grader-service

WORKDIR /var/lib/grader-service

ENTRYPOINT ["tini", "-g", "--"]
CMD ["grader_service.sh" ]