#!/bin/bash -e

# Generating mock app.config
sed -e "s|{{FYRE_CLUSTER_DOMAIN}}|$FYRE_CLUSTER_DOMAIN|" \
-e "s|{{FYRE_CLUSTER_USER_EMAIL}}|$FYRE_CLUSTER_USER_EMAIL|" \
-e "s|{{FYRE_CLUSTER_USER_PASSWORD}}|$FYRE_CLUSTER_USER_PASSWORD|" \
$PATH_MOCK_APP_CONFIG > $TRAVIS_BUILD_DIR/mock_app.config

cat $TRAVIS_BUILD_DIR/mock_app.config

sleep $FYRE_DEPLOY_SLEEP_SECONDS

tox -c ./resilient-sdk -e INT
