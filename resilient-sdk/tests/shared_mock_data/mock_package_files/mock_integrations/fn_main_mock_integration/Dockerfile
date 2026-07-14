# Generated with resilient-sdk v51.0.1.0.0
# docker build -t ibmresilient/fn_main_mock_integration:1.0.0 .
ARG BASE_IMAGE_REPO=quay.io
ARG BASE_IMAGE_TAG=latest

FROM ${BASE_IMAGE_REPO}/ibmresilient/soarapps-base-docker-image:${BASE_IMAGE_TAG}

ARG APPLICATION=fn_main_mock_integration

# install the base package
COPY ./dist /tmp/packages
USER 0
RUN yum -y update && yum clean all
# pip is bootstrapped via ensurepip and removed after install to resolve PRISMA-2022-0168 (CVE-2018-20225)
RUN python3 -m ensurepip --upgrade && \
    python3 -m pip install /tmp/packages/${APPLICATION}-*.tar.gz && \
    python3 -m pip uninstall -y pip setuptools
USER 1001
