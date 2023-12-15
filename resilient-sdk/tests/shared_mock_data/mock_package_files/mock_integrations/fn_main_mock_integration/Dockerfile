# Generated with resilient-sdk v51.0.1.0.0
# docker build -t ibmresilient/fn_main_mock_integration:1.0.0 .
ARG BASE_IMAGE_REPO=quay.io
ARG BASE_IMAGE_TAG=latest

FROM ${BASE_IMAGE_REPO}/ibmresilient/soarapps-base-docker-image:${BASE_IMAGE_TAG}

ARG APPLICATION=fn_main_mock_integration

# install the base package
COPY ./dist /tmp/packages
RUN pip install /tmp/packages/${APPLICATION}-*.tar.gz
