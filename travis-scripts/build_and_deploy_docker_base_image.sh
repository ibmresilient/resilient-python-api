# Build and publish "soarapps-base-docker-image" base docker image.
# example use in Travis:
#     ./build_and_deploy_docker_base_image.sh "quay.io" $NEW_VERSION
# Pre-requisite: logged into docker repo intending to push to.
# Requires passing the DOCKER_REPO_PATH and CIRCUITS_VESRION as
# command line args.
# Also requires $TRAVIS_BUILD_DIR as a env variable that is the path to the
# python-api repo.

# Tags Created (assuming NEW_VESRION=v51.0.0.0.1234)
#  - latest
#  - v51.0.0.0.1234
#  - python-311
#  - v51.0.0.0.1234-python-311
#  - python-39
#  - v51.0.0.0.1234-python-39

DOCKER_REPO_PATH=$1 # ex: docker-eu.artifactory.swg-devops.com/sec-resilient-docker-local OR quay.io
CIRCUITS_VERSION=$2

###############
## Functions ##
###############
print_msg () {
    printf "\n--------------------\n$1\n--------------------\n"
}

###########
## Start ##
###########
print_msg "\
DOCKER_REPO_PATH:\t\t${DOCKER_REPO_PATH}\n\
DOCKER_IMAGE_NAME:\t\t${DOCKER_IMAGE_NAME}\n\
CIRCUITS_VERSION:\t\t${CIRCUITS_VERSION}\n\
"

tag_base="${DOCKER_REPO_PATH}/ibmresilient/${DOCKER_IMAGE_NAME}"
tag_version="${tag_base}:${CIRCUITS_VERSION}"
tag_latest="${tag_base}:latest"
tag_version_39="${tag_base}:${CIRCUITS_VERSION}-python-39"
tag_python_39="${tag_base}:python-39"
tag_version_311="${tag_base}:${CIRCUITS_VERSION}-python-311"
tag_python_311="${tag_base}:python-311"

# build PY311 and tag appropriately with "<version>", "<version>-python-311", "python-311", "latest"
docker build -t ${tag_version} -t ${tag_version_311} -t ${tag_python_311} -t ${tag_latest} \
    --build-arg RESILIENT_CIRCUITS_VERSION=${CIRCUITS_VERSION} \
    --build-arg PYTHON_VERSION=python-311 \
    ${TRAVIS_BUILD_DIR}

# build PY39 version and tag with "<version>-python-39", "python-39"
docker build -t ${tag_version_39} -t ${tag_python_39} \
    --build-arg RESILIENT_CIRCUITS_VERSION=${CIRCUITS_VERSION} \
    --build-arg PYTHON_VERSION=python-39 \
    ${TRAVIS_BUILD_DIR}

# push all versions to their tagged location
docker push ${tag_base} --all-tags
