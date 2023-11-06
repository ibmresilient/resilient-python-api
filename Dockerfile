# docker build -t quay.io/ibmresilient/soarapps-base-docker-image:${NEW_VERSION} -t quay.io/ibmresilient/soarapps-base-docker-image:latest --build-arg RESILIENT_CIRCUITS_VERSION=${NEW_VERSION} --build-arg PYTHON_VERSION=python-311 --build-arg UBI_VERSION=ubi9 .

###########################
### START BUILDER IMAGE ###
###########################

# REQUIRED: set RESILIENT_CIRCUITS_VERSION when you build by passing: --build-arg RESILIENT_CIRCUITS_VERSION=<version>
ARG RESILIENT_CIRCUITS_VERSION
# OPTIONAL: set PYTHON_VERSION when you build by passing: --build-arg PYTHON_VERSION=python-39|python-311
# default: python-39
ARG PYTHON_VERSION=python-39
# OPTIONAL: set UBI_VERSION when you build by passing: --build-arg UBI_VERSION=ubi8|ubi9|ubi10
# default: ubi9
ARG UBI_VERSION=ubi9

# Builder image (this stage only used to build circuits and its dependencies)
FROM registry.access.redhat.com/${UBI_VERSION}/${PYTHON_VERSION}:latest AS builder

ARG RESILIENT_CIRCUITS_VERSION

# use root user to build
USER 0

# copy all packages and contents over to temporary build packages folder
COPY . /tmp/builder_packages/resilient-python-api
# upgrade pip and install build
RUN pip install -U pip build

# build each package and copy to wheels directory for use in next stage
WORKDIR /tmp/builder_packages/resilient-python-api
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${RESILIENT_CIRCUITS_VERSION}
RUN mkdir /tmp/builder_packages/wheels && \
    python -m build -w -o /tmp/builder_packages/wheels resilient-app-config-plugins && \
    python -m build -w -o /tmp/builder_packages/wheels resilient && \
    python -m build -w -o /tmp/builder_packages/wheels resilient-lib && \
    python -m build -w -o /tmp/builder_packages/wheels resilient-circuits

#########################
### END BUILDER IMAGE ###
#########################

########################
### START MAIN IMAGE ###
########################

# Base image using Red Hat's universal base image (default UBI9) for python
FROM registry.access.redhat.com/${UBI_VERSION}/${PYTHON_VERSION}:latest

ARG PATH_RESILIENT_CIRCUITS=rescircuits

# root priviledges to set up the structure
USER 0

# create arbitrary group for user 1001
RUN groupadd -g 1001 default && usermod -g 1001 default

# set up configuration and log locations using /etc and /var/log, the conventional locations for config and logs
RUN mkdir /etc/${PATH_RESILIENT_CIRCUITS} && \
    # setup entrypoint for read-only enterprise data used by integration, if needed
    mkdir /var/${PATH_RESILIENT_CIRCUITS} && \
    # entrypoint for resilient-circuits
    mkdir /opt/${PATH_RESILIENT_CIRCUITS} && \
    # create directory for logs
    mkdir /var/log/${PATH_RESILIENT_CIRCUITS} && \
    # allow access by non root processes
    # See https://docs.openshift.com/container-platform/4.2/openshift_images/create-images.html#images-create-guide-openshift_create-images
    chgrp -R 1001 /var/log/${PATH_RESILIENT_CIRCUITS} && \
    chmod -R g=u /var/log/${PATH_RESILIENT_CIRCUITS}

# required ENVIRONMENT variables
ENV APP_HOST_CONTAINER=1
ENV APP_CONFIG_FILE=/etc/${PATH_RESILIENT_CIRCUITS}/app.config
ENV APP_LOG_DIR /var/log/${PATH_RESILIENT_CIRCUITS}

# update yum and pip
RUN yum -y update && yum clean all && pip install --upgrade pip

# copy over the built packages and install them then immediately remove them
COPY --from=builder /tmp/builder_packages/wheels /tmp/packages
RUN pip install /tmp/packages/*${RESILIENT_CIRCUITS_VERSION}*.whl && \
    rm -rf /tmp/packages

# copy over and set the entrypoint
COPY docker_template_entrypoint.sh /opt/${PATH_RESILIENT_CIRCUITS}/entrypoint.sh
ENTRYPOINT [ "sh", "/opt/rescircuits/entrypoint.sh" ]

# set user to 1001
USER 1001

######################
### END MAIN IMAGE ###
######################
