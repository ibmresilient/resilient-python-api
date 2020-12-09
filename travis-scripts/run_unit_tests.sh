#!/bin/bash -e

tox -c ./resilient-circuits
tox -c ./resilient-sdk
tox -c ./resilient-lib