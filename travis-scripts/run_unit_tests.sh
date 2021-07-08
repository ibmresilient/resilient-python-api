#!/bin/bash -e

tox -c ./resilient
tox -c ./resilient-circuits
tox -c ./resilient-sdk -e UNIT
tox -c ./resilient-lib