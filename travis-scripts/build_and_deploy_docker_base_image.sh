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
#  - python-312
#  - v51.0.0.0.1234-python-312

DOCKER_REPO_PATH=$1 # ex: docker-eu.artifactory.swg-devops.com/sec-resilient-docker-local OR quay.io
CIRCUITS_VERSION=$2

pipeline_type="$(get_env pipeline_namespace)"

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
tag_version_311="${tag_base}:${CIRCUITS_VERSION}-python-311"
tag_python_311="${tag_base}:python-311"
tag_version_312="${tag_base}:${CIRCUITS_VERSION}-python-312"
tag_python_312="${tag_base}:python-312"

# build PY311 and tag appropriately with "<version>", "<version>-python-311", "python-311", "latest"
PY311_DIGEST=`docker build -t ${tag_version} -t ${tag_version_311} -t ${tag_python_311} -t ${tag_latest} \
    --quiet \
    --build-arg RESILIENT_CIRCUITS_VERSION=${CIRCUITS_VERSION} \
    --build-arg PYTHON_VERSION=python-311 \
    ${TRAVIS_BUILD_DIR}`

# build PY312 version and tag with "<version>-python-312", "python-312"
PY311_DIGEST=`docker build -t ${tag_version_312} -t ${tag_python_312} \
    --quiet \
    --build-arg RESILIENT_CIRCUITS_VERSION=${CIRCUITS_VERSION} \
    --build-arg PYTHON_VERSION=python-312 \
    ${TRAVIS_BUILD_DIR}`

echo "TRAVIS_EVENT_TYPE: $TRAVIS_EVENT_TYPE, TRIGGER_TYPE: $TRIGGER_TYPE"

if [ $TRAVIS_EVENT_TYPE == "cron" ||  "$TRIGGER_TYPE" == "timer" ]; then # TODO : remove Travis reference
    # when running on a CRON build, only push the latest, and two Python versions
    docker push ${tag_latest}
    docker push ${tag_python_311}
    docker push ${tag_python_312}
else
    # push all versions to their tagged location
    docker push ${tag_base} --all-tags
fi

if [ -n "$pipeline_type" ]; then # TODO: remove this check when we're off Travis
    echo "Running on SPS..."
    # TODO: Uncomment the below chunk when we are ready to start saving artifacts for image scans.
    # save_artifact "${DOCKER_IMAGE_NAME}:${tag_python_311}" type=image "name=${tag_python_311}" "digest=${PY311_DIGEST}" "${CIRCUITS_VERSION}-python-311"
    # save_artifact "${DOCKER_IMAGE_NAME}:${tag_python_312}" type=image "name=${tag_python_312}" "digest=${PY312_DIGEST}" "${CIRCUITS_VERSION}-python-312"
else
    echo "Running on Travis..."
fi