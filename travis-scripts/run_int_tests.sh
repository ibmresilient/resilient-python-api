#!/bin/bash -e

PATH_MOCK_APP_CONFIG="$TRAVIS_BUILD_DIR/travis-scripts/mock_app_config"

sed -e "s|{{FYRE_CLUSTER_DOMAIN}}|$FYRE_CLUSTER_DOMAIN|" \
-e "s|{{FYRE_CLUSTER_API_KEY_ID}}|$FYRE_CLUSTER_API_KEY_ID|" \
-e "s|{{FYRE_CLUSTER_API_KEY_SECRET}}|$FYRE_CLUSTER_API_KEY_SECRET|" \
$PATH_MOCK_APP_CONFIG > $TRAVIS_BUILD_DIR/mock_app.config

cat $TRAVIS_BUILD_DIR/mock_app.config

sleep $FYRE_DEPLOY_SLEEP_SECONDS

tox -c ./resilient-sdk -e INT
