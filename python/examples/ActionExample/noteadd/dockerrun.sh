#!/bin/bash
docker run --name $2 -v /home/cme/Action/logs/Action:/code/logs  -d --restart=always $1
