from __future__ import print_function
import argparse
import pytest
import doctest
import time
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

class TestCo3Patch:
    """Tests for patch, create_patch, and get_patch methods"""
    def _connect(self, co3_args):
        uri = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = co3.SimpleClient(org_name=co3_args.org,
                                  base_url=uri,
                                  verify=False)
        assert client
        user_info = client.connect(co3_args.email, co3_args.password)
        assert user_info
        return client

    def _create_incident(self, client, incident_dict):
        """create a test incident to use for patching"""
        incident = {"name": __name__,
                    "discovered_date": int(time.time() * 1000)
        }
        incident.update(incident_dict)
        inc = client.post("/incidents", incident)
        return inc

    @pytest.mark.parametrize("overwrite_conflict", (True, False))
    def test_patch_conflict(self, co3_args, overwrite_conflict):
        """ do incident patch that results in conflict """
        client = self._connect(co3_args)
        inc = self._create_incident(client, {"name": "test"})
        uri = "/incidents/%d" % inc['id']
        # Create a conflict
        inc["name"] = "the wrong value"
        patch = client.create_patch(inc, {"name": "test updated"})
        patch["version"] = patch["version"] - 1 # Force it to check old_value
        try:
            response = client.patch(uri, patch, overwrite_conflict=overwrite_conflict)
            assert(overwrite_conflict)
            assert response["success"] is True
            inc = client.get("/incidents/%d" % inc['id'])
            assert inc['name'] == "test updated"

        except co3.co3.SimpleHTTPException as e:
            assert(not overwrite_conflict)
            fail_msg = "could not be applied due to a conflicting edit by another user.  The following field(s) were in conflict:  name."
            assert fail_msg in e.response.json()["message"]

    def test_patch_no_conflict(self, co3_args):
        """ do incident_patch with no conflict """
        client = self._connect(co3_args)
        inc = self._create_incident(client, {"name": "test"})
        uri = "/incidents/%d" % inc['id']
        patch = client.create_patch(inc, {"name": "test updated"})
        response = client.patch(uri, patch, overwrite_conflict=False)
        assert response["success"] is True
        inc = client.get("/incidents/%d" % inc['id'])
        assert inc['name'] == "test updated"

    @pytest.mark.parametrize("existing", ("yes", "no", "partial"))
    def test_get_patch_without_existing(self, co3_args, existing):
        """get_patch with missing or incomplete existing_obj"""
        def get_update_dict(inc):
            return {"name": "test updated"}

        client = self._connect(co3_args)
        inc = self._create_incident(client, {"name": "test"})
        uri = "/incidents/%d" % inc['id']
        if existing == "no":
            existing_object = None
        else:
            existing_object = inc
        if existing == "partial":
            # Remove the parts we'd be checking
            existing_object.pop("vers")
            existing_object.pop("name")

        response = client.get_patch(uri, get_update_dict, existing_object=existing_object,
                                    retry_on_conflict=True)
        assert response["success"] is True
        inc = client.get("/incidents/%d" % inc['id'])
        assert inc['name'] == "test updated"

    @pytest.mark.parametrize("conflict_retry", (True, False))
    def test_get_patch_conflict(self, co3_args, conflict_retry):
        """ do incident get_patch that results in conflict"""
        def get_update_dict(inc):
            return {"name": "test updated"}

        client = self._connect(co3_args)
        inc = self._create_incident(client, {"name": "test"})
        uri = "/incidents/%d" % inc['id']
        # Create a conflict
        inc["name"] = "the wrong value"
        inc["vers"] = inc["vers"] - 1
        try:
            response = client.get_patch(uri, get_update_dict, existing_object=inc,
                                        retry_on_conflict=conflict_retry)
            assert(conflict_retry)
            assert response["success"] is True
            inc = client.get("/incidents/%d" % inc['id'])
            assert inc['name'] == "test updated"

        except co3.co3.SimpleHTTPException as e:
            assert(not conflict_retry)
            fail_msg = "could not be applied due to a conflicting edit by another user.  The following field(s) were in conflict:  name."
            assert fail_msg in e.response.json()["message"]

    def test_get_patch_no_conflict(self, co3_args):
        """ do incident get_patch with no conflict """
        def get_update_dict(inc):
            return {"name": "test updated"}

        client = self._connect(co3_args)
        inc = self._create_incident(client, {"name": "test"})
        uri = "/incidents/%d" % inc['id']
        response = client.get_patch(uri, get_update_dict, existing_object=inc,
                                    retry_on_conflict=False)
        assert response["success"] is True
        inc = client.get("/incidents/%d" % inc['id'])
        assert inc['name'] == "test updated"
