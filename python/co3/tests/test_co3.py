from __future__ import print_function
import argparse
import shlex
import pytest
import co3
import co3.co3argparse

@pytest.fixture(scope="session")
def co3_args(request):
    print("co3_args fixture")
    config_file = request.config.getoption("--config-file")
    co3args = request.config.getoption("--co3args")
    co3args = shlex.split(co3args)

    args= co3.co3argparse.ArgumentParser(config_file=config_file).parse_args(args=co3args)
    return args

class TestCo3:
    def test_connect_no_verify(self, co3_args):
        """ Successful connection with no Cert Verification """
        url = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = co3.SimpleClient(org_name=co3_args.org,
                                  base_url=url,
                                  verify=False)
        assert client
        userinfo = client.connect(co3_args.email, co3_args.password)
        assert userinfo
