#!/bin/bash -e

# param $1: (required) branch name to push to. Accepted values are: ALL, gh-pages or main.

###############
## Variables ##
###############
BRANCHES_TO_SYNC=$1

DO_NOT_SYNC=(
'.github'
'.scripts'
'.pre-commit-config.yaml'
'.secrets.baseline'
'.whitesource'
'sonar-project.properties'
)

cd $app_repo_dir

###############
## Functions ##
###############
print_msg () {
    printf "\n--------------------\n$1\n--------------------\n"
}

sync_branch() {
    # param $1: source branch name to sync from
    # param $2: target branch name to sync to

    cd $app_repo_dir

    source_branch=$1
    target_branch=$2

    print_msg "Syncing INTERNAL '$source_branch' branch with PUBLIC '$target_branch' branch"
    git clone --branch=$source_branch "https://$GITHUB_AUTH_TOKEN@github.ibm.com/Resilient/resilient-python-api.git" "$source_branch-dir"
    cd "$source_branch-dir"
    git checkout $source_branch
    git fetch && git pull

    # clear files we don't want to sync
    for item in "${DO_NOT_SYNC[@]}"; do
        rm -f -R $item
    done

    git add -A
    git diff-index --quiet HEAD || git commit -m "Syncing external repository on $(date +%F)"

    git push -f https://$GITHUB_AUTH_TOKEN_PUBLIC@github.com/ibmresilient/resilient-python-api.git $source_branch:$target_branch

    cd $app_repo_dir
}

###########
## Start ##
###########
print_msg "\
BRANCHES_TO_SYNC:\t$BRANCHES_TO_SYNC \n\
"

if [ "$BRANCHES_TO_SYNC" == "ALL" ] || [ "$BRANCHES_TO_SYNC" == "main" ] ; then
    sync_branch "master" "main"
fi

if [ "$BRANCHES_TO_SYNC" == "ALL" ] || [ "$BRANCHES_TO_SYNC" == "gh-pages" ] ; then
    sync_branch "gh-pages" "gh-pages"
fi

cd $app_repo_dir
