# !/bin/bash -e

# param $1: (required)
# param $2: (optional)

# Dependencies on:
# sudo apt-get install jq

###############
## Variables ##
###############
FYRE_ACTION=$1
FYRE_API_URL="api.fyre.ibm.com/rest/v1"
FYRE_API_KEY=$FYRE_API_KEY_SHANE
FYRE_USERNAME=$FYRE_USERNAME_SHANE
FYRE_CLUSTER_STATUS=""
FYRE_REQUEST_ID=""

###############
## Functions ##
###############
print_msg () {
    printf "\n--------------------\n$1\n--------------------\n"
}

get_quota_info () {
    # param $1: (required) FYRE product_group_id
    # param $2: (required) FYRE account user email address

    print_msg "Getting quota info for the user '${2}' in the product_group: ${1}"
    CURL_RES=$(curl -X GET -s -k -u $FYRE_USERNAME:$FYRE_API_KEY "https://$FYRE_API_URL/?operation=getuserproductgroupquota&product_group_id=${1}&user_email=$2")
    printf "\n--------------------\n"
    echo $CURL_RES | json_pp
    printf "\n--------------------\n"
}

get_cluster_info () {
    # param $1: (required) FYRE request_id

    print_msg "Getting cluster info for request_id: ${1}"
    CURL_RES=$(curl -X GET -s -k -u $FYRE_USERNAME:$FYRE_API_KEY "https://$FYRE_API_URL/?operation=query&request=showrequests&request_id=${1}")
    printf "\n--------------------\n"
    echo $CURL_RES | json_pp
    printf "\n--------------------\n"
    FYRE_CLUSTER_STATUS=$(echo $CURL_RES | jq -r ".request[0].status")
}

deploy_stencil () {
    # param $1: (required) FYRE stencil_id
    # param $1: (required) FYRE cluster_prefix

    DEPLOY_STENCIL_DATA="{\"type\":\"stencil\", \"stencil_id\":\"$1\", \"cluster_prefix\" : \"$2\"}"
    print_msg "Deploying stencil: $DEPLOY_STENCIL_DATA"
    CURL_RES=$(curl -X POST -s -k -u $FYRE_USERNAME:$FYRE_API_KEY "https://$FYRE_API_URL/?operation=build" --data "$DEPLOY_STENCIL_DATA")
    printf "\n--------------------\n"
    echo $CURL_RES | json_pp
    printf "\n--------------------\n"
    FYRE_REQUEST_ID=$(echo $CURL_RES | jq -r ".request_id")
}

delete_cluster () {
    # param $1: (required) FYRE cluster_prefix

    DELETE_CLUSTER_DATA="{\"cluster_name\":\"$1\"}"
    print_msg "Deleting cluster: $DELETE_CLUSTER_DATA"
    CURL_RES=$(curl -X POST -s -k -u $FYRE_USERNAME:$FYRE_API_KEY "https://$FYRE_API_URL/?operation=delete" --data "$DELETE_CLUSTER_DATA")
    printf "\n--------------------\n"
    echo $CURL_RES | json_pp
    printf "\n--------------------\n"
}

build_and_run_cluster () {
    # param $1: (required) FYRE_STENCIL_ID
    # param $2: (required) FYRE_CLUSTER_NAME
    # param $3: (required) FYRE_CLUSTER_DOMAIN
    # param $4: (required) FYRE_DEPLOY_SLEEP_SECONDS
    # param $5: (required) FYRE_DEPLOY_TIMEOUT_SECONDS

    FYRE_STENCIL_ID=$1
    FYRE_CLUSTER_NAME=$2
    FYRE_CLUSTER_DOMAIN=$3
    FYRE_DEPLOY_SLEEP_SECONDS=$4
    FYRE_DEPLOY_TIMEOUT_SECONDS=$5

    deploy_stencil "$FYRE_STENCIL_ID" "$FYRE_CLUSTER_NAME"
    get_cluster_info "$FYRE_REQUEST_ID"
    print_msg "FYRE_CLUSTER_STATUS: ${FYRE_CLUSTER_STATUS}"

    NOW=$(date +"%s")

    while [ "$FYRE_CLUSTER_STATUS" != "completed" ] ; do
        print_msg "Sleeping for ${FYRE_DEPLOY_SLEEP_SECONDS}s"
        sleep $FYRE_DEPLOY_SLEEP_SECONDS

        get_cluster_info "$FYRE_REQUEST_ID"
        print_msg "FYRE_CLUSTER_STATUS: ${FYRE_CLUSTER_STATUS}"

        if [ "$FYRE_CLUSTER_STATUS" == "error" ] ; then
            print_msg "ERROR: failed to deploy stencil"
            exit 1
        fi

        CURRENT_SECONDS=$(date +"%s")
        SECONDS_PASSED=$(($CURRENT_SECONDS-$NOW))
        print_msg "SECONDS_PASSED: $SECONDS_PASSED"

        if [ "$SECONDS_PASSED" -gt "$FYRE_DEPLOY_TIMEOUT_SECONDS" ] ; then
            print_msg "ERROR: Timeout of ${FYRE_DEPLOY_TIMEOUT_SECONDS}s reached"
            exit 1
        fi
    done

    print_msg "Stencil ${FYRE_STENCIL_ID} deployed and running at https://${FYRE_CLUSTER_DOMAIN}/"
}

###########
## Start ##
###########
print_msg "\
FYRE_ACTION:\t\t\t$FYRE_ACTION \n\
FYRE_API_URL:\t\t\t$FYRE_API_URL \n\
FYRE_USERNAME:\t\t\t$FYRE_USERNAME \n\
FYRE_CLUSTER_NAME:\t\t$FYRE_CLUSTER_NAME \n\
FYRE_CLUSTER_DOMAIN:\t\t$FYRE_CLUSTER_DOMAIN \n\
FYRE_STENCIL_ID:\t\t$FYRE_STENCIL_ID \n\
FYRE_REQUEST_ID:\t\t$FYRE_REQUEST_ID \n\
FYRE_DEPLOY_SLEEP_SECONDS:\t$FYRE_DEPLOY_SLEEP_SECONDS \n\
FYRE_DEPLOY_TIMEOUT_SECONDS:\t$FYRE_DEPLOY_TIMEOUT_SECONDS \
"

case $FYRE_ACTION in 

    QUOTA_INFO)
    # param $2: FYRE product_group_id
    # param $3: FYRE account user email address
    get_quota_info $2 $3
    ;;

    CLUSTER_INFO)
    # param $2: FYRE request_id
    get_cluster_info $2
    ;;

    DEPLOY)
    build_and_run_cluster $FYRE_STENCIL_ID $FYRE_CLUSTER_NAME $FYRE_CLUSTER_DOMAIN $FYRE_DEPLOY_SLEEP_SECONDS $FYRE_DEPLOY_TIMEOUT_SECONDS
    ;;

    DELETE)
    # param $2: FYRE cluster_prefix
    delete_cluster $2
    ;;

    *)
    print_msg "ERROR: Unsupported FYRE Action: ${FYRE_ACTION}" 
    ;;
esac
