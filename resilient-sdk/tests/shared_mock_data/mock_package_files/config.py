# -*- coding: utf-8 -*-

"""Generate a default configuration-file section for fn_main_mock_integration"""


def config_section_data():
    """
    Produce add the default configuration section to app.config,
    for fn_main_mock_integration when called by `resilient-circuits config [-c|-u]`
    """
    config_data = None

    config_data = u"""[fn_main_mock_integration]
username = <<enter_user_email_here>>
api_Key=dfghjFGYuy4567890nbvcghj
password = GJ^&*(';lkjhgfd567&*()_)

# Some random comments here
# and here

config_option=True

[other_section]
unicode_entry = ઘ ઙ ચ છ જ ઝ ઞ
"""
    return config_data
