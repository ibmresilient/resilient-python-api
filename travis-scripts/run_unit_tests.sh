#!/bin/bash -e

tox -c ./resilient -- -m "not livetest"
tox -c ./resilient-circuits -- -m "not livetest"
tox -c ./resilient-sdk -e UNIT -- -m "not livetest"
tox -c ./resilient-lib -- -m "not livetest"