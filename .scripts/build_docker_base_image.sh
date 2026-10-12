#!/bin/bash
set -euo pipefail

## ----------------------------------------------------------------------------
## build_docker_base_image.sh
## ----------------------------------------------------------------------------
## Description:
##   Builds the "soarapps-base-docker-image" base images:
##     UBI9-minimal  (default): Python 3.12
##     UBI10-minimal (opt-in):  Python 3.12, 3.13, 3.14
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
##   - docker-eu.artifactory.swg-devops.com/sec-resilient-docker-local/ibmresilient/soarapps-base-docker-image
##   - quay.io/ibmresilient/soarapps-base-docker-image
##   - docker-na-public.artifactory.swg-devops.com/sec-isc-team-isc-icp-docker-local/soarapps-base-docker-image (CVE scanning only)
##
## Tags Created (example: CIRCUITS_VERSION=v51.0.0.0.1234):
##   UBI9-minimal (default):
##   - latest
##   - v51.0.0.0.1234
##   - python-312
##   - v51.0.0.0.1234-python-312
##   - Dev_v51.0.0.0.1234-python-312 (CVE scanning only)
##
##   UBI10-minimal (opt-in):
##   - ubi10-min-py312
##   - v51.0.0.0.1234-ubi10-min-py312
##   - ubi10-min-py313
##   - v51.0.0.0.1234-ubi10-min-py313
##   - ubi10-min-py314
##   - v51.0.0.0.1234-ubi10-min-py314
##   - Dev_v51.0.0.0.1234-ubi10-min-py312 (CVE scanning only)
##   - Dev_v51.0.0.0.1234-ubi10-min-py313 (CVE scanning only)
##   - Dev_v51.0.0.0.1234-ubi10-min-py314 (CVE scanning only)
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

readonly RESILIENT_ARTIFACTORY_REPOSITORY="${RESILIENT_ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME}/${RESILIENT_ARTIFACTORY_DOCKER_REPO_NAME}/ibmresilient/${DOCKER_IMAGE_NAME}"
readonly QUAY_REPOSITORY="${QUAY_DOCKER_REGISTRY_BASE_NAME}/ibmresilient/${DOCKER_IMAGE_NAME}"
readonly ARTIFACTORY_REPOSITORY="${ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME}/${ARTIFACTORY_DOCKER_REPO_NAME}/${DOCKER_IMAGE_NAME}"  # only used for CVE scanning

build_and_tag_docker_image() {
    local python_version="${1:-3.12}"           # full patch version, e.g. 3.12.0 or 3.13.5; defaults to 3.12
    local ubi_version="${2:-ubi9-minimal}"      # UBI base image version; defaults to ubi9-minimal
    shift 2
    local tag_variants=("$@")
    local tags=()

    for repo in "${repositories[@]}"; do
        for tag in "${tag_variants[@]}"; do
            tags+=(-t "${repo}:${tag}")
        done
    done

    # retag the images so they can be scanned for CVEs
    tags+=(-t "${ARTIFACTORY_REPOSITORY}:Dev_${CIRCUITS_VERSION}-${ubi_version}-${python_version}")

    docker build \
        "${tags[@]}" \
        --build-arg "RESILIENT_CIRCUITS_VERSION=${CIRCUITS_VERSION}" \
        --build-arg "PYTHON_VERSION=${python_version}" \
        --build-arg "UBI_VERSION=${ubi_version}" \
        --build-arg "ARTIFACTORY_API_TOKEN=${ARTIFACTORY_API_TOKEN}" \
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

# UBI9-minimal tags (Python 3.12 only)
ubi9_min_python312_tags=(
    "${CIRCUITS_VERSION}"
    "${CIRCUITS_VERSION}-ubi9-min-py312"
    "ubi9-min-py312"
    "latest"
)

# UBI10-minimal tags (Python 3.12, 3.13, 3.14)
ubi10_min_python312_tags=(
    "${CIRCUITS_VERSION}-ubi10-min-py312"
    "ubi10-min-py312"
)

ubi10_min_python313_tags=(
    "${CIRCUITS_VERSION}-ubi10-min-py313"
    "ubi10-min-py313"
)

ubi10_min_python314_tags=(
    "${CIRCUITS_VERSION}-ubi10-min-py314"
    "ubi10-min-py314"
)

# All PYTHON_VERSION values are full patch versions — Python is installed from UBI-specific Artifactory tarballs.
# Update these when new patch tarballs are uploaded to Artifactory.
PYTHON_312_VERSION="3.12.14"
PYTHON_313_VERSION="3.13.15"
PYTHON_314_VERSION="3.14.7"

# Build UBI9-minimal images
ubi9_min_python312_digest=$(build_and_tag_docker_image "${PYTHON_312_VERSION}" "ubi9-minimal" "${ubi9_min_python312_tags[@]}")

# Build UBI10-minimal images
ubi10_min_python312_digest=$(build_and_tag_docker_image "${PYTHON_312_VERSION}" "ubi10-minimal" "${ubi10_min_python312_tags[@]}")
ubi10_min_python313_digest=$(build_and_tag_docker_image "${PYTHON_313_VERSION}" "ubi10-minimal" "${ubi10_min_python313_tags[@]}")
ubi10_min_python314_digest=$(build_and_tag_docker_image "${PYTHON_314_VERSION}" "ubi10-minimal" "${ubi10_min_python314_tags[@]}")

print_msg "Docker images built..."
docker images

tags_to_push=()

echo "TRIGGER_TYPE: ${TRIGGER_TYPE}"
if [[ "${TRIGGER_TYPE}" == "timer" ]]; then
    # when running on a timed build, only push the unversioned tags
    tags_to_push=("latest" "ubi9-min-py312" "ubi10-min-py312" "ubi10-min-py313" "ubi10-min-py314")
else
    # push all versions to their tagged location
    tags_to_push=("${ubi9_min_python312_tags[@]}" "${ubi10_min_python312_tags[@]}" "${ubi10_min_python313_tags[@]}" "${ubi10_min_python314_tags[@]}")
fi

if [[ "$SHOULD_DEPLOY_ARTIFACTORY" -eq 0 ]]; then
    push_tags "$RESILIENT_ARTIFACTORY_REPOSITORY"
fi

if [[ "$SHOULD_RELEASE_QUAY" -eq 0 ]]; then
    push_tags "$QUAY_REPOSITORY"
fi

# TODO: Uncomment the below chunk when we are ready to start saving artifacts for CVE scanning
# ubi9_min_python_312_tag_to_scan="${ARTIFACTORY_REPOSITORY}:Dev_${CIRCUITS_VERSION}-python-312"
# ubi10_min_python_312_tag_to_scan="${ARTIFACTORY_REPOSITORY}:Dev_${CIRCUITS_VERSION}-ubi10-py312"
# ubi10_min_python_313_tag_to_scan="${ARTIFACTORY_REPOSITORY}:Dev_${CIRCUITS_VERSION}-ubi10-py313"
# ubi10_min_python_314_tag_to_scan="${ARTIFACTORY_REPOSITORY}:Dev_${CIRCUITS_VERSION}-ubi10-py314"

# docker push "${ubi9_min_python_312_tag_to_scan}"
# docker push "${ubi10_min_python_312_tag_to_scan}"
# docker push "${ubi10_min_python_313_tag_to_scan}"
# docker push "${ubi10_min_python_314_tag_to_scan}"

# save_artifact "${ubi9_min_python_312_tag_to_scan}" type=image "name=${ubi9_min_python_312_tag_to_scan}" "digest=${python312_digest}" "${CIRCUITS_VERSION}-python-312"
# save_artifact "${ubi10_min_python_312_tag_to_scan}" type=image "name=${ubi10_min_python_312_tag_to_scan}" "digest=${ubi10_min_python312_digest}" "${CIRCUITS_VERSION}-ubi10-py312"
# save_artifact "${ubi10_min_python_313_tag_to_scan}" type=image "name=${ubi10_min_python_313_tag_to_scan}" "digest=${ubi10_min_python313_digest}" "${CIRCUITS_VERSION}-ubi10-py313"
# save_artifact "${ubi10_min_python_314_tag_to_scan}" type=image "name=${ubi10_min_python_314_tag_to_scan}" "digest=${ubi10_min_python314_digest}" "${CIRCUITS_VERSION}-ubi10-py314"