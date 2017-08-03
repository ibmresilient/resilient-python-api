from __future__ import print_function
import argparse
import pytest
import doctest
import types
import co3


class TestCo3:

    def test_doctest(self):
        """Run doctest on all modules, even if you didn't --doctest-modules"""
        for item in co3.__dict__.values():
            if type(item) is types.ModuleType:
                doctest.testmod(item, verbose=True, raise_on_error=True)

    def test_connect_no_verify(self, co3_args):
        """ Successful connection with no Cert Verification """
        url = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = co3.SimpleClient(org_name=co3_args.org,
                                  base_url=url,
                                  verify=False)
        assert client
        userinfo = client.connect(co3_args.email, co3_args.password)
        assert userinfo

    def test_connect_proxy(self, co3_args):
        """ Successful connection with no Cert Verification """
        url = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = co3.SimpleClient(org_name=co3_args.org,
                                  base_url=url,
                                  verify=False,
                                  proxies=co3_args.proxy)
        assert client
        user_info = client.connect(co3_args.email, co3_args.password)
        assert user_info

