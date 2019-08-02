#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

""" TODO: module docstring """

import logging

LOG = logging.getLogger("resilient_sdk_log")
LOG.setLevel(logging.INFO)
LOG.addHandler(logging.StreamHandler())


def main():
    LOG.info("resilient-sdk started...")

if __name__ == "__main__":
    main()
