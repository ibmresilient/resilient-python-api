#!/bin/bash
set -euo pipefail

## ----------------------------------------------------------------------------
## build_docker_base_image.sh
## ----------------------------------------------------------------------------
## Description:
##   Builds the Python 3.11 and 3.12 "soarapps-base-docker-image" base images.
##   The script tags, retags, and optionally pushes these images to the
##   appropriate repositories. It also creates "Dev" tags for CVE scanning and
##   saves them as build artifacts.
##
## Arguments:
##   $1 - CIRCUITS_VERSION: The version of resilient-circuits to use.
##   $2 - SHOULD_DEPLOY_ARTIFACTORY: 1 or 0 flag to control pushing to Artifactory.
##   $3 - SHOULD_RELEASE_QUAY: 1 or 0 flag to control pushing to Quay.
##
## Example:
##   ./build_docker_base_image.sh "v51.0.0.0.1234" 1 0
##
## Repositories:
##   - docker-na-public.artifactory.swg-devops.com/sec-resilient-docker-local/ibmresilient/soarapps-base-docker-image
##   - quay.io/ibmresilient/soarapps-base-docker-image
##   - docker-na-public.artifactory.swg-devops.com/sec-isc-team-isc-icp-docker-local/soarapps-base-docker-image (CVE scanning only)
##
## Tags Created (example: CIRCUITS_VERSION=v51.0.0.0.1234):
##   - latest
##   - v51.0.0.0.1234
##   - python-311
##   - v51.0.0.0.1234-python-311
##   - python-312
##   - v51.0.0.0.1234-python-312
##   - Dev_v51.0.0.0.1234-python-311 (CVE scanning only)
##   - Dev_v51.0.0.0.1234-python-312 (CVE scanning only)
##
## Prerequisites:
##   - Logged into Artifactory and Quay registries.
##   - The following environment variables must be set:
##       - ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME
##       - RESILIENT_ARTIFACTORY_DOCKER_REPO_NAME
##       - DOCKER_IMAGE_NAME
##       - QUAY_DOCKER_REGISTRY_BASE_NAME
##       - ARTIFACTORY_DOCKER_REPO_NAME
##       - app_repo_dir
##       - TRIGGER_TYPE (set by SPS)
## ----------------------------------------------------------------------------

readonly CIRCUITS_VERSION="$1"
readonly SHOULD_DEPLOY_ARTIFACTORY="$2"
readonly SHOULD_RELEASE_QUAY="$3"

readonly RESILIENT_ARTIFACTORY_REPOSITORY="${ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME}/${RESILIENT_ARTIFACTORY_DOCKER_REPO_NAME}/ibmresilient/${DOCKER_IMAGE_NAME}"
readonly QUAY_REPOSITORY="${QUAY_DOCKER_REGISTRY_BASE_NAME}/ibmresilient/${DOCKER_IMAGE_NAME}"
readonly ARTIFACTORY_REPOSITORY="${ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME}/${ARTIFACTORY_DOCKER_REPO_NAME}/${DOCKER_IMAGE_NAME}"  # only used for CVE scanning

build_and_tag_docker_image() {
    local python_version="$1"; shift
    local tag_variants=("$@")
    local tags=()

    for repo in "${repositories[@]}"; do
        for tag in "${tag_variants[@]}"; do
            tags+=(-t "${repo}:${tag}")
        done
    done

    # retag the images so they can be scanned for CVEs
    tags+=(-t "${ARTIFACTORY_REPOSITORY}:Dev_${CIRCUITS_VERSION}-${python_version}")

    docker build \
        "${tags[@]}" \
        --quiet \
        --build-arg "RESILIENT_CIRCUITS_VERSION=${CIRCUITS_VERSION}" \
        --build-arg "PYTHON_VERSION=${python_version}" \
        "${app_repo_dir}"
}

print_msg() {
    printf "\n--------------------\n%s\n--------------------\n" "$1"
}

push_tags() {
    local repo="$1"
    shift

    for tag in "${tags_to_push[@]}"; do
        echo "Pushing ${repo}:${tag}"
        docker push "${repo}:${tag}"
    done
}

repositories=(
    "$RESILIENT_ARTIFACTORY_REPOSITORY"
    "$QUAY_REPOSITORY"
)

python311_tags=(
    "${CIRCUITS_VERSION}"
    "${CIRCUITS_VERSION}-python-311"
    "python-311"
    "latest"
)

python312_tags=(
    "${CIRCUITS_VERSION}-python-312"
    "python-312"
)

python311_digest=$(build_and_tag_docker_image "python-311" "${python311_tags[@]}")
python312_digest=$(build_and_tag_docker_image "python-312" "${python312_tags[@]}")

print_msg "Docker images built..."
docker images

tags_to_push=()

echo "TRIGGER_TYPE: ${TRIGGER_TYPE}"
if [[ "${TRIGGER_TYPE}" == "timer" ]]; then
    # when running on a timed build, only push the latest, and two Python versions
    tags_to_push=("latest" "python-311" "python-312")
else
    # push all versions to their tagged location
    tags_to_push=("${python311_tags[@]}" "${python312_tags[@]}")
fi

if [[ "$SHOULD_DEPLOY_ARTIFACTORY" -eq 0 ]]; then
    push_tags "$RESILIENT_ARTIFACTORY_REPOSITORY"
fi

if [[ "$SHOULD_RELEASE_QUAY" -eq 0 ]]; then
    push_tags "$QUAY_REPOSITORY"
fi

# TODO: Uncomment the below chunk when we are ready to start saving artifacts for CVE scanning
# python_311_tag_to_scan="${ARTIFACTORY_REPOSITORY}:Dev_${CIRCUITS_VERSION}-python-311"
# python_312_tag_to_scan="${ARTIFACTORY_REPOSITORY}:Dev_${CIRCUITS_VERSION}-python-312"

# docker push "${python_311_tag_to_scan}"
# docker push "${python_312_tag_to_scan}"

# save_artifact "${python_311_tag_to_scan}" type=image "name=${python_311_tag_to_scan}" "digest=${python_311_digest}" "${CIRCUITS_VERSION}-python-311"
# save_artifact "${python_312_tag_to_scan}" type=image "name=${python_312_tag_to_scan}" "digest=${python_312_digest}" "${CIRCUITS_VERSION}-python-312"