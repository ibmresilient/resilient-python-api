#!/bin/bash -e

tox -c ./resilient-circuits
tox -c ./resilient-sdk/tests/unit
tox -c ./resilient-lib