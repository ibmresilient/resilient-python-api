# -*- coding: utf-8 -*-

"""Generate a default configuration-file section for all integrations to use when proxies are involved"""


def config_section_data():
    """Produce the default configuration section for app.config,
       when called by `resilient-circuits config [-c|-u]`
    """
    config_data = u"""[integrations]
http_proxy=
https_proxy=
"""
    return config_data