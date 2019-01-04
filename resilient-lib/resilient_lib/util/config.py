# -*- coding: utf-8 -*-

"""Generate a default configuration-file section for all integrations to use when proxies are involved"""


def config_section_data():
    """Produce the default configuration section for app.config,
       when called by `resilient-circuits config [-c|-u]`
    """
    config_data = u"""[integrations]
# These proxy settings will be used by all integrations. 
# To override, add http_proxy= and https_proxy= to your specific integration section
http_proxy=
https_proxy=
"""
    return config_data