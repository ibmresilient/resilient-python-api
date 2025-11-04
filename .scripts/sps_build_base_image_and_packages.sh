#!/bin/bash

set -euo pipefail

# functions
function print_msg () {
    printf "\n--------------------\n%s\n--------------------\n" "$1"
}

function debug_python_environment(){
    local python_version=$1

    if [[ "$DEBUG_PYTHON_ENVIRONMENT" == "true" ]]; then
        python"${python_version}" --version
        command -v "python"${python_version}" --version"

        echo "command -v \"python${python_version}\""
        command -v "python${python_version}"

        echo "pip list"
        pip list
    fi
}

repo_login() {
    local registry="$1" user="$2" token="$3"

    print_msg "Logging user ${user} into registry ${registry}"
    echo "$token" | docker login --password-stdin --username "$user" "https://${registry}/"
}

print_msg "Trigger type for GitHub branch $BRANCH: $TRIGGER_TYPE"

# helper functions
is_master_branch()      { [[ "$BRANCH" == "$GIT_MASTER_BRANCH" ]]; }
is_release_branch()     { [[ "$BRANCH" =~ $GIT_RELEASE_BRANCH_REGEX ]]; }
is_pages_branch()       { [[ "$BRANCH" =~ $GIT_PAGES_BRANCH_REGEX ]]; }
is_timer_trigger()      { [[ "$TRIGGER_TYPE" == "timer" ]]; }
is_scm_trigger()        { [[ "$TRIGGER_TYPE" == "scm" ]]; }

is_core_branch() { is_master_branch || is_release_branch; }
should_build_packages() { ! is_pages_branch; }                                                      # only for master, release branches and PRs
should_deploy_artifactory() { ! is_timer_trigger && is_core_branch; }                               # only for master and release branches, not timed jobs
should_deploy_docs() { ! is_timer_trigger && { is_pages_branch || is_core_branch; }; }              # only for master, release/.. or pages/... branches, not timed jobs
should_release_pypi() { is_scm_trigger && is_master_branch; }                                       # only for release/pypi/... branches
should_release_quay() { should_release_pypi || { is_timer_trigger && is_master_branch; }; }         # only for release/pypi/... branches OR timed jobs building master

# paths
app_repo_dir="$WORKSPACE/$(load_repo app-repo path)"
PATH_SCRIPTS_DIR="$app_repo_dir/.scripts"
PATH_COMMON_SCRIPTS_DIR="$app_repo_dir/common_scripts"
PATH_TEMPLATE_PYPIRC="$PATH_SCRIPTS_DIR/template.pypirc"

# docker config
DOCKER_IMAGE_NAME="soarapps-base-docker-image"
ARTIFACTORY_DOCKER_REPO_NAME="$(get_env ARTIFACTORY_DOCKER_REPO_NAME)"
RESILIENT_ARTIFACTORY_DOCKER_REPO_NAME="$(get_env RESILIENT_ARTIFACTORY_DOCKER_REPO_NAME)"
ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME="$(get_env ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME)"
RESILIENT_ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME="$(get_env RESILIENT_ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME)"
QUAY_USERNAME="ibmresilient"
QUAY_PASSWORD="$(get_env QUAY_PASSWORD)"
QUAY_DOCKER_REGISTRY_BASE_NAME="$(get_env QUAY_DOCKER_REGISTRY_BASE_NAME)"

# artifactory & pypi config
ARTIFACTORY_USERNAME="$(get_env ARTIFACTORY_USERNAME)"
ARTIFACTORY_API_TOKEN="$(get_env ARTIFACTORY_API_TOKEN)"
ARTIFACTORY_PYPI_REPO_URL="$(get_env ARTIFACTORY_PYPI_REPO_URL)"
ARTIFACTORY_REPO_URL=https://na.artifactory.swg-devops.com/artifactory/sec-resilient-team-integrations-generic-local/resilient-python-api
PYPI_API_KEY="$(get_env PYPI_API_KEY)"

# git variables
GIT_MASTER_BRANCH="master"
GIT_RELEASE_BRANCH_REGEX="^release/.+"
GIT_PAGES_BRANCH_REGEX="^pages/.+"

PAGES_INTERNAL_LINK="https://pages.github.ibm.com/Resilient/resilient-python-api/"
PAGES_PUBLIC_LINK="https://ibm.biz/soar-python-docs"

# build info
LATEST_TAG=$(git describe --abbrev=0 --tags)
IS_MASTER=$([[ "$BRANCH" != *"master"* ]]; echo $?)
IS_RELEASE=$([[ "$BRANCH" != *"release/"* ]]; echo $?)
LIB_VERSION=`if [[ $IS_RELEASE -eq 1 ]]; then echo $(echo ${BRANCH##*/} | cut -d "." -f 1,2,3,4); else echo $(echo $LATEST_TAG | cut -d "." -f 1,2,3,4); fi`
NEW_VERSION="${LIB_VERSION}.${BUILD_NUMBER}"
ARTIFACTORY_LIB_LOCATION="${ARTIFACTORY_REPO_URL}/${LIB_VERSION}/${NEW_VERSION}"
SETUPTOOLS_SCM_PRETEND_VERSION=$NEW_VERSION
DEBUG_PYTHON_ENVIRONMENT="$(get_env debug_python_environment)"

# auth
GITHUB_AUTH_TOKEN="$(get_env GITHUB_AUTH_TOKEN)"                    # FID for github.ibm.com
GITHUB_AUTH_TOKEN_PUBLIC="$(get_env GITHUB_AUTH_TOKEN_PUBLIC)"      # FID for github.com
NOTIFICATION_HOOK="$(get_env NOTIFICATION_HOOK)"

export app_repo_dir
export ARTIFACTORY_API_TOKEN
export ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME
export ARTIFACTORY_DOCKER_REPO_NAME
export ARTIFACTORY_LIB_LOCATION
export ARTIFACTORY_PYPI_REPO_URL
export ARTIFACTORY_USERNAME
export DOCKER_IMAGE_NAME
export GITHUB_AUTH_TOKEN
export GITHUB_AUTH_TOKEN_PUBLIC
export NOTIFICATION_HOOK
export PATH_TEMPLATE_PYPIRC
export PYPI_API_KEY
export RESILIENT_ARTIFACTORY_DOCKER_REPO_NAME
export RESILIENT_ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME
export SETUPTOOLS_SCM_PRETEND_VERSION
export QUAY_DOCKER_REGISTRY_BASE_NAME

# common scripts use python command rather than python3 - create a symbolic link
sudo ln -s /usr/bin/python3 /usr/local/bin/python

# install python to call script to upload .tgz file to artifactory
source "$WORKSPACE/$PIPELINE_CONFIG_REPO_PATH/scripts/utilities/python_utils.sh"
install_python3 "3.11"
debug_python_environment "3.11"

# required python packages
pip install requests retry2 twine build jinja2 sphinx furo sphinx-copybutton

# configure GitHub user
git config --global user.name "soar-apps"
git config --global user.email "soar-apps@ibm.com"

build_packages(){
    print_msg "Building packages in Python 3.11 for GitHub branch $BRANCH, trigger $TRIGGER_TYPE"
    "$PATH_SCRIPTS_DIR"/build_and_deploy_packages.sh no_deploy    
}

build_and_deploy_base_images(){
    print_msg "Building soarapps-base-docker-image"
    repo_login "${RESILIENT_ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME}" "${ARTIFACTORY_USERNAME}" "${ARTIFACTORY_API_TOKEN}"
    repo_login "${ARTIFACTORY_DOCKER_REGISTRY_BASE_NAME}" "${ARTIFACTORY_USERNAME}" "${ARTIFACTORY_API_TOKEN}"
    repo_login "${QUAY_DOCKER_REGISTRY_BASE_NAME}" "${QUAY_USERNAME}" "${QUAY_PASSWORD}"
    "$PATH_SCRIPTS_DIR"/build_docker_base_image.sh "${NEW_VERSION}" "$(should_deploy_artifactory; echo $?)" "$(should_release_quay; echo $?)"
}

deploy_packages_to_artifactory(){
    print_msg "Deploying packages to Artifactory for GitHub branch $BRANCH, trigger $TRIGGER_TYPE"
    "$PATH_SCRIPTS_DIR"/build_and_deploy_packages.sh do_deploy

    print_msg "Sending notification to Slack"
    PARSED_VERSION=$(echo "$NEW_VERSION" | cut -d "v" -f 2)
    "$PATH_COMMON_SCRIPTS_DIR"/send_slack_notification_sps.sh "Link to Artifactory - <$ARTIFACTORY_LIB_LOCATION|$NEW_VERSION> \n Install command - \`\`\`pip install -U <package-name>==$PARSED_VERSION -i https://<EMAIL_ADDRESS>:<ARTIFACTORY_ACCESS_TOKEN>@na.artifactory.swg-devops.com/artifactory/api/pypi/sec-resilient-team-integrations-pypi-virtual/simple\`\`\` " "success"
}

deploy_internall_documentation(){
    print_msg "Deploying documentation internally for GitHub branch $BRANCH, trigger $TRIGGER_TYPE"
    "$PATH_SCRIPTS_DIR"/build_and_deploy_packages.sh no_deploy no_release deploy_docs

    print_msg "Deploying to GitHub Pages..."
    "$PATH_SCRIPTS_DIR"/deploy_documentation.sh
    "$PATH_COMMON_SCRIPTS_DIR"/send_slack_notification_sps.sh "INTERNAL Docs for $NEW_VERSION have been published and are available at <$PAGES_INTERNAL_LINK|$PAGES_INTERNAL_LINK>" "success";
}

release_to_pypi(){
    print_msg "Releasing to PYPI for GitHub branch $BRANCH, trigger $TRIGGER_TYPE"
    "$PATH_SCRIPTS_DIR"/build_and_deploy_packages.sh no_deploy do_release

    print_msg "Sending notification to Slack"
    "$PATH_COMMON_SCRIPTS_DIR"/send_slack_notification.sh "Successfully released $NEW_VERSION to PyPi" "success"

    # create GitHub tag
    repo_dir="resilient-python-api-directory"
    git clone --branch "$BRANCH" "https://$GITHUB_AUTH_TOKEN@github.ibm.com/Resilient/resilient-python-api.git" $repo_dir
    
    cd $repo_dir
    git tag -a "release/pypi/${NEW_VERSION}" -m "Releasing version ${NEW_VERSION} to PyPi" && git push --follow-tags
    cd ../ && rm -r $repo_dir
}

sync_publi_repos(){
    print_msg "Syncing public repo for GitHub branch $BRANCH, trigger $TRIGGER_TYPE"
    "$PATH_SCRIPTS_DIR"/sync_public_repo.sh "ALL"
    "$PATH_COMMON_SCRIPTS_DIR"/send_slack_notification.sh "PUBLIC Docs for $NEW_VERSION have been published and are available at <$PAGES_PUBLIC_LINK|$PAGES_PUBLIC_LINK>" "success";
}

# build Packages in Python 3.11
if should_build_packages; then
    build_packages
else
    print_msg "Skipping building packages in Python 3.11 for GitHub branch $BRANCH, trigger $TRIGGER_TYPE"
fi

# build soarapps-base-docker-image
build_and_deploy_base_images

# deploy packages to Artifactory and deploy Docker base image to Artifactory
if should_deploy_artifactory; then
    deploy_packages_to_artifactory
else
    print_msg "Skipping deploying packages to Artifactory for GitHub branch $BRANCH, trigger $TRIGGER_TYPE"
fi

# deploy documentation
if should_deploy_docs; then
    deploy_internall_documentation
else
    print_msg "Skipping deploying documentation for GitHub branch $BRANCH, trigger $TRIGGER_TYPE"
fi

# release to Pypi and sync public repos
if should_release_pypi; then
    release_to_pypi
    sync_publi_repos
else
    print_msg "Skipping releasing to PYPI and syncing public repo for GitHub branch $BRANCH, trigger $TRIGGER_TYPE"
fi
