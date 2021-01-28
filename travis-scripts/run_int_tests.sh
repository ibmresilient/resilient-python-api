#!/bin/bash -e

PATH_MOCK_APP_CONFIG="$TRAVIS_BUILD_DIR/travis-scripts/mock_app.config"

sed -e "s|{{FYRE_CLUSTER_DOMAIN}}|myresilient1.fyre.ibm.com|" \
-e "s|{{FYRE_CLUSTER_API_KEY_ID}}|$FYRE_CLUSTER_API_KEY_ID|" \
-e "s|{{FYRE_CLUSTER_API_KEY_SECRET}}|$FYRE_CLUSTER_API_KEY_SECRET|" \
$PATH_MOCK_APP_CONFIG > $TRAVIS_BUILD_DIR/mock_app.config

tox -c ./resilient-sdk -e INT
