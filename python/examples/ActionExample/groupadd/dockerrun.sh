#!/bin/bash
docker run --name cmeaction -v /home/cme/Action/logs/Action:/code/logs  -d --restart=always sbade:cmeaction
