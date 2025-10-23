#!/bin/bash

DOCKER_REPO_PATH=$1
CIRCUITS_VERSION=$2

# functions
print_msg () {
    printf "\n--------------------\n$1\n--------------------\n"
}

print_msg "\
DOCKER_REPO_PATH:\t\t${DOCKER_REPO_PATH}\n\
DOCKER_IMAGE_NAME:\t\t${DOCKER_IMAGE_NAME}\n\
CIRCUITS_VERSION:\t\t${CIRCUITS_VERSION}\n\
"

tag_base="${DOCKER_REPO_PATH}/${DOCKER_IMAGE_NAME}"

tag_version="${tag_base}:Dev_${CIRCUITS_VERSION}"
tag_version_311="${tag_version}-python-311"
tag_version_312="${tag_version}-python-312"

# build PY311 and tag appropriately with "<version>-python-311"
PY311_DIGEST=`docker build -t ${tag_version_311} \
    --quiet \
    --build-arg RESILIENT_CIRCUITS_VERSION=${CIRCUITS_VERSION} \
    --build-arg PYTHON_VERSION=python-311 \
    ${TRAVIS_BUILD_DIR}`

# build PY312 version and tag with "<version>-python-312"
PY312_DIGEST=`docker build -t ${tag_version_312} \
    --quiet \
    --build-arg RESILIENT_CIRCUITS_VERSION=${CIRCUITS_VERSION} \
    --build-arg PYTHON_VERSION=python-312 \
    ${TRAVIS_BUILD_DIR}`

echo "tag_version_311: $tag_version_311, PY311_DIGEST: ${PY311_DIGEST}"
echo "tag_version_312: $tag_version_312, PY312_DIGEST: ${PY312_DIGEST}"

docker push ${tag_version_311}
docker push ${tag_version_312}

# TODO: Uncomment the below chunk when we are ready to start saving artifacts for image scans.
#save_artifact "${tag_version_311}" type=image "name=${tag_version_311}" "digest=${PY311_DIGEST}" "${CIRCUITS_VERSION}-python-311"
#save_artifact "${tag_version_312}" type=image "name=${tag_version_312}" "digest=${PY312_DIGEST}" "${CIRCUITS_VERSION}-python-312"
