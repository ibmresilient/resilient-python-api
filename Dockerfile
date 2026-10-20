# UBI9  (default): docker build ... --build-arg RESILIENT_CIRCUITS_VERSION=${NEW_VERSION} --build-arg PYTHON_VERSION=3.12.14 --build-arg ARTIFACTORY_API_TOKEN=<token> .
# UBI10 (opt-in):  docker build ... --build-arg UBI_VERSION=ubi10-minimal --build-arg PYTHON_VERSION=3.13.15 --build-arg ARTIFACTORY_API_TOKEN=<token> --build-arg RESILIENT_CIRCUITS_VERSION=${NEW_VERSION} .

# REQUIRED: set RESILIENT_CIRCUITS_VERSION when you build by passing: --build-arg RESILIENT_CIRCUITS_VERSION=<version>
ARG RESILIENT_CIRCUITS_VERSION
# OPTIONAL: set UBI_VERSION when you build by passing: --build-arg UBI_VERSION=ubi9-minimal|ubi10-minimal
# default: ubi9-minimal (ubi10-minimal opt-in; enables Python 3.13 and 3.14)
ARG UBI_VERSION=ubi9-minimal
# OPTIONAL: Python version to install — always pass the full patch version, e.g. 3.12.14 or 3.13.15.
# Python is installed from a UBI-specific Artifactory tarball; check Artifactory for available versions.
ARG PYTHON_VERSION=3.12.14

############################
### START PYTHON BASE    ###
############################

# Installs Python from a UBI-specific Artifactory tarball (e.g. python3.12.14-ubi9-minimal-x86_64.tar.gz).
# PYMINOR is derived from PYTHON_VERSION (e.g. 3.12.14 -> 3.12) and used for binary paths.
# bzip2-libs libffi expat sqlite-libs are runtime deps for the tarball-installed Python.
# curl-minimal is pre-installed on UBI9/UBI10; tar and gzip are installed temporarily and removed after extraction.
FROM registry.access.redhat.com/${UBI_VERSION}:latest AS python-base

ARG UBI_VERSION=ubi9-minimal
ARG PYTHON_VERSION=3.12.14
ARG ARTIFACTORY_API_TOKEN

USER 0

RUN if [ -z "${ARTIFACTORY_API_TOKEN}" ]; then \
        echo "ERROR: ARTIFACTORY_API_TOKEN build arg is required but was not set." >&2; \
        exit 1; \
    fi && \
    PYMINOR=$(echo ${PYTHON_VERSION} | cut -d. -f1,2) && \
    PYBIN=/usr/local/bin/python${PYMINOR} && \
    PIPBIN=/usr/local/bin/pip${PYMINOR} && \
    microdnf install -y bzip2-libs libffi expat sqlite-libs tar gzip && \
    microdnf clean all && \
    curl --fail -L \
        -H "Authorization: Bearer ${ARTIFACTORY_API_TOKEN}" \
        -o /tmp/python.tar.gz \
        "https://na.artifactory.swg-devops.com/artifactory/sec-resilient-team-integrations-generic-local/python_tarballs/python${PYTHON_VERSION}-${UBI_VERSION}-x86_64.tar.gz" && \
    tar xzf /tmp/python.tar.gz -C /usr/local && \
    rm /tmp/python.tar.gz && \
    microdnf remove -y tar gzip && microdnf clean all && \
    if [ ! -x "${PYBIN}" ] || [ ! -x "${PIPBIN}" ]; then \
        echo "ERROR: Python ${PYTHON_VERSION} could not be installed from Artifactory." >&2; \
        exit 1; \
    fi && \
    alternatives --install /usr/bin/python3 python3 ${PYBIN} 1 && \
    alternatives --install /usr/bin/python  python  ${PYBIN} 1 && \
    alternatives --install /usr/bin/pip     pip     ${PIPBIN} 1

##########################
### END PYTHON BASE     ###
##########################

###########################
### START BUILDER IMAGE ###
###########################

# Builder image (this stage only used to build circuits and its dependencies)
FROM python-base AS builder

ARG RESILIENT_CIRCUITS_VERSION

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

# Base image using Red Hat's UBI minimal image (ubi9-minimal by default, ubi10-minimal opt-in)
FROM python-base

ARG RESILIENT_CIRCUITS_VERSION
ARG PATH_RESILIENT_CIRCUITS=rescircuits
# PYTHON_VERSION must be the same as the version used in PYTHON-BASE stage
ARG PYTHON_VERSION=3.12.14 

# Install shadow-utils and procps-ng; symlink yum -> microdnf for downstream app Dockerfiles.
RUN microdnf install -y shadow-utils procps-ng && \
    microdnf clean all && \
    ln -s /usr/bin/microdnf /usr/bin/yum

# create arbitrary group and user 1001 (ubi9-minimal has no 'default' user pre-created)
# -m creates /home/default; resilient-circuits needs a writable ~ to create ~/.resilient
RUN groupadd -g 1001 default && \
    (id 1001 &>/dev/null && usermod -g 1001 $(id -nu 1001) || useradd -u 1001 -g 1001 -m -s /sbin/nologin default)

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
# purge pip files so app Dockerfiles can cleanly re-bootstrap pip via ensurepip
# /tmp/packages contains exactly the four wheels built in this run — no version glob needed
COPY --from=builder /tmp/builder_packages/wheels /tmp/packages
RUN PYMINOR=$(echo ${PYTHON_VERSION} | cut -d. -f1,2) && \
    pip install --upgrade pip setuptools && \
    pip install /tmp/packages/*.whl && \
    rm -rf /tmp/packages && \
    pip uninstall -y pip setuptools && \
    rm -rf /usr/local/lib/python${PYMINOR}/site-packages/pip \
           /usr/local/lib/python${PYMINOR}/site-packages/pip-*.dist-info \
           /usr/local/lib/python${PYMINOR}/site-packages/pip-*.egg-info \
           /usr/bin/pip /usr/bin/pip3

# copy over and set the entrypoint
COPY docker_template_entrypoint.sh /opt/${PATH_RESILIENT_CIRCUITS}/entrypoint.sh
ENTRYPOINT [ "sh", "/opt/rescircuits/entrypoint.sh" ]

# set user to 1001
USER 1001

######################
### END MAIN IMAGE ###
######################
