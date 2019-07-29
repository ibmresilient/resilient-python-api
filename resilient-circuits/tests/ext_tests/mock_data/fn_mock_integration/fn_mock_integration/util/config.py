# -*- coding: utf-8 -*-

"""Generate a default configuration-file section for fn_mock_integration"""

from __future__ import print_function


def config_section_data():
    """Produce the default configuration section for app.config,
       when called by `resilient-circuits config [-c|-u]`
    """
    config_data = u"""[fn_mock_integration_sec_one]
mock_config_url=https://api.example.com
mock_config_username=aryastark@example.com
#mock_config_timeout=300
mock_config_password=TheK!ghtKing

[fn_mock_integration_sec_two]
#mock_config_proxy_http=
mock_config_proxy_https=https://example.com
"""
    return config_data
