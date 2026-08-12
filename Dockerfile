# docker build -t quay.io/ibmresilient/soarapps-base-docker-image:${NEW_VERSION} -t quay.io/ibmresilient/soarapps-base-docker-image:latest --build-arg RESILIENT_CIRCUITS_VERSION=${NEW_VERSION} --build-arg PYTHON_SHORT_VERSION=3.12 --build-arg UBI_VERSION=ubi9-minimal .

###########################
### START BUILDER IMAGE ###
###########################

# REQUIRED: set RESILIENT_CIRCUITS_VERSION when you build by passing: --build-arg RESILIENT_CIRCUITS_VERSION=<version>
ARG RESILIENT_CIRCUITS_VERSION
# OPTIONAL: set UBI_VERSION when you build by passing: --build-arg UBI_VERSION=ubi9|ubi10
# default: ubi9-minimal
ARG UBI_VERSION=ubi9-minimal

# Builder image (this stage only used to build circuits and its dependencies)
FROM registry.access.redhat.com/${UBI_VERSION}:latest AS builder

ARG RESILIENT_CIRCUITS_VERSION
ARG PYTHON_SHORT_VERSION=3.12

# use root user to build
USER 0

# install python and pip
# NOTE: python3.12 is available via microdnf on ubi9-minimal; python3.13+ is not — upgrading PYTHON_SHORT_VERSION
# will require pulling a tarball from Artifactory and building from source instead of this microdnf install
RUN microdnf install -y python${PYTHON_SHORT_VERSION} python${PYTHON_SHORT_VERSION}-pip && microdnf clean all && \
    alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_SHORT_VERSION} 1 && \
    alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_SHORT_VERSION} 1 && \
    alternatives --install /usr/bin/pip pip /usr/bin/pip${PYTHON_SHORT_VERSION} 1

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

# Base image using Red Hat's universal base image with python installed
FROM registry.access.redhat.com/${UBI_VERSION}:latest

ARG PATH_RESILIENT_CIRCUITS=rescircuits
ARG PYTHON_SHORT_VERSION=3.12

# root priviledges to set up the structure
USER 0

# install python; symlink yum -> microdnf so app Dockerfiles need no changes
# NOTE: python3.12 is available via microdnf on ubi9-minimal; python3.13+ is not — upgrading PYTHON_SHORT_VERSION
# will require pulling a tarball from Artifactory and building from source instead of this microdnf install
RUN microdnf install -y python${PYTHON_SHORT_VERSION} python${PYTHON_SHORT_VERSION}-pip shadow-utils && microdnf clean all && \
    alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_SHORT_VERSION} 1 && \
    alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_SHORT_VERSION} 1 && \
    alternatives --install /usr/bin/pip pip /usr/bin/pip${PYTHON_SHORT_VERSION} 1 && \
    ln -s /usr/bin/microdnf /usr/bin/yum

# create arbitrary group and user 1001 (ubi9-minimal has no 'default' user pre-created)
RUN groupadd -g 1001 default && \
    (id 1001 &>/dev/null && usermod -g 1001 $(id -nu 1001) || useradd -u 1001 -g 1001 -M -s /sbin/nologin default)

# set up configuration and log locations using /etc and /var/log, the conventional locations for config and logs
RUN mkdir /etc/${PATH_RESILIENT_CIRCUITS} && \
    # data directory for read-only enterprise data used by integration, if needed
    mkdir /var/${PATH_RESILIENT_CIRCUITS} && \
    # directory for the entrypoint script
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

# update and remove unneeded packages
RUN microdnf -y update && microdnf clean all
RUN microdnf -y remove httpd httpd-tools httpd-core httpd-filesystem httpd-devel \
              mod_ssl mod_lua mod_ldap mod_session mod_http2 mod_auth_gssapi || true

# copy over the built packages, install them, remove temp files, then remove pip
# purge the RPM-owned pip files so app Dockerfiles can cleanly re-bootstrap pip via ensurepip
COPY --from=builder /tmp/builder_packages/wheels /tmp/packages
RUN pip install --upgrade pip setuptools && \
    pip install /tmp/packages/*${RESILIENT_CIRCUITS_VERSION}*.whl && \
    rm -rf /tmp/packages && \
    pip uninstall -y pip setuptools && \
    rm -rf /usr/lib/python${PYTHON_SHORT_VERSION}/site-packages/pip \
           /usr/lib/python${PYTHON_SHORT_VERSION}/site-packages/pip-*.dist-info \
           /usr/lib/python${PYTHON_SHORT_VERSION}/site-packages/pip-*.egg-info \
           /usr/bin/pip /usr/bin/pip3 /usr/bin/pip${PYTHON_SHORT_VERSION} /usr/bin/pip-${PYTHON_SHORT_VERSION}

# copy over and set the entrypoint
COPY docker_template_entrypoint.sh /opt/${PATH_RESILIENT_CIRCUITS}/entrypoint.sh
ENTRYPOINT [ "sh", "/opt/rescircuits/entrypoint.sh" ]

# set user to 1001
USER 1001

######################
### END MAIN IMAGE ###
######################
