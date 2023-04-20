#!/bin/bash -e

PATH_PACKAGE=$1
PACKAGE_NAME=$2

rm */dist/*
rm $PATH_PACKAGE/temp/*

cd resilient-app-config-plugins
python -m build
cd ../resilient
python -m build
cd ../resilient-lib
python -m build
cd ../resilient-circuits
python -m build
cd ..

cp ./*/dist/*.whl $PATH_PACKAGE/temp

docker build $PATH_PACKAGE -t docker-na.artifactory.swg-devops.com/sec-resilient-team-integrations-docker-local/boregistry/$PACKAGE_NAME:1.0.0
docker push docker-na.artifactory.swg-devops.com/sec-resilient-team-integrations-docker-local/boregistry/$PACKAGE_NAME:1.0.0
