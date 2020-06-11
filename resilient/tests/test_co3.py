# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.
from __future__ import print_function
import pytest
import doctest
import time
import types
import os
import resilient
from argparse import ArgumentParser
from mock import patch
from shutil import rmtree

DEFAULT_CONFIG_FILENAME = "app.config"
DEFAULT_CONFIG_FILE = os.path.expanduser(os.path.join("~", ".resilient", DEFAULT_CONFIG_FILENAME))

def mock_os_path_exists(path):
    return True

def mock_os_path_not_exists(path):
    return False

def mock_makedirs(dir):
    pass

class TestCo3:
    """Basic API tests"""

    def test_doctest(self):
        """Run doctest on all modules, even if you didn't --doctest-modules"""
        for item in resilient.__dict__.values():
            if type(item) is types.ModuleType:
                doctest.testmod(item, verbose=True, raise_on_error=True)

    def test_connect_no_verify(self, co3_args):
        """ Successful connection with no Cert Verification """
        url = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = resilient.SimpleClient(org_name=co3_args.org,
                                        base_url=url,
                                        verify=False)
        assert client
        userinfo = client.connect(co3_args.email, co3_args.password)
        assert userinfo

    def test_connect_proxy(self, co3_args):
        """ Successful connection with no Cert Verification """
        url = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = resilient.SimpleClient(org_name=co3_args.org,
                                        base_url=url,
                                        verify=False,
                                        proxies=co3_args.proxy)
        assert client
        user_info = client.connect(co3_args.email, co3_args.password)
        assert user_info

    @pytest.mark.parametrize("resp", ([], None))
    def test_extract_org_id_failure(self, co3_args, resp):
        """Extract org id given org name"""
        url = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = resilient.SimpleClient(org_name=co3_args.org,
                                        base_url=url,
                                        verify=False,
                                        proxies=co3_args.proxy)
        try:
            client._extract_org_id({"orgs": resp})
            assert False
        except Exception as e:
            assert True

    def test_org_error(self, co3_args):
        """No org entered"""
        url = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = resilient.SimpleClient(org_name=co3_args.org,
                                        base_url=url,
                                        verify=False,
                                        proxies=co3_args.proxy)
        # Mismatch.
        try:
            client._extract_org_id({"orgs": [{"name": "Fake Org"}]})
            assert False
        except Exception as e:
            assert True

        # not enabled
        try:
            client._extract_org_id({"orgs": [{"name": client.org_name,
                                              "enabled": False}]})
            assert False
        except Exception as e:
            assert True

        # Erase org_name input
        client.org_name = None
        try:
            client._extract_org_id({"orgs": [{"name": "Fake Org"}]})
            assert False
        except Exception as e:
            assert True

    def test_api_key(self, co3_args):
        """
        Test using api key to get org
        :return:
        """
        print(str(co3_args))
        url = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = resilient.SimpleClient(org_name=co3_args.org,
                                        base_url=url,
                                        verify=False,
                                        proxies=co3_args.proxy)
        if (co3_args.api_key_id is not None and co3_args.api_key_secret is not None):
            try:
                # Erase org_id
                client.org_id = None
                ret = client.set_api_key(co3_args.api_key_id, co3_args.api_key_secret)
                assert client.org_id
            except Exception as e:
                assert False


class TestCo3Patch:
    """Tests for patch, create_patch, and get_patch methods"""
    def _connect(self, co3_args):
        uri = "https://{0}:{1}".format(co3_args.host, co3_args.port or 443)
        client = resilient.SimpleClient(org_name=co3_args.org,
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
        inc["vers"] -= 1 # Force it to check old_value
        patch = resilient.Patch(inc)
        patch.add_value("name", "test updated")

        if overwrite_conflict:
            # If overwrite_conflict is specified then patch will return.
            response = client.patch(uri, patch, overwrite_conflict=overwrite_conflict)

            assert resilient.PatchStatus(response.json()).is_success() is overwrite_conflict
        else:
            # Not overwriting conflict, so an exception will be thrown.
            with pytest.raises(resilient.PatchConflictException) as exception_info:
                client.patch(uri, patch, overwrite_conflict=overwrite_conflict)

            # Gather the patch_status value from the exception for additional verification.
            patch_status = exception_info.value.patch_status

            fail_msg = "could not be applied due to a conflicting edit by another user.  The following field(s) were in conflict:  name."
            assert fail_msg in patch_status.get_message()

            assert patch_status.get_conflict_fields() == ["name"]
            assert patch_status.get_your_original_value("name") == "the wrong value"
            assert patch_status.get_actual_current_value("name") == "test"

        inc = client.get("/incidents/%d" % inc['id'])

        if overwrite_conflict:
            assert inc['name'] == "test updated"
        else:
            assert inc['name'] == "test"

    def test_patch_no_conflict(self, co3_args):
        """ do incident_patch with no conflict """
        client = self._connect(co3_args)
        inc = self._create_incident(client, {"name": "test"})
        uri = "/incidents/%d" % inc['id']
        patch = resilient.Patch(inc)
        patch.add_value("name", "test updated")
        response = client.patch(uri, patch, overwrite_conflict=False)
        assert resilient.PatchStatus(response.json()).is_success()
        inc = client.get("/incidents/%d" % inc['id'])
        assert inc['name'] == "test updated"

    def test_patch_null_old_value(self, co3_args):
        client = self._connect(co3_args)

        inc = self._create_incident(client, {"name": "test", "description": None})

        patch = resilient.Patch(inc)

        patch.add_value("description", "new value")

        uri = "/incidents/%d" % inc['id']

        response = client.patch(uri, patch)

        inc = client.get("/incidents/%d" % inc['id'])

        assert inc["description"] == "new value"

    def test_patch_invalid_callback(self, co3_args):
        """
        If a callback returns True but didn't modify the passed in patch in any way, that'd be a problem.
        So make sure we throw an exception in that case.
        """
        client = self._connect(co3_args)

        inc = self._create_incident(client, {"name": "test"})

        uri = "/incidents/%d" % inc['id']

        # Create a conflict
        inc["name"] = "the wrong value"
        inc["vers"] -= 1 # Force it to check old_value

        patch = resilient.Patch(inc)

        patch.add_value("name", "test updated")

        def mycb(response, patch_status, patch):
            # Return True but don't modify the patch.
            return True

        with pytest.raises(ValueError) as exception_info:
            client.patch_with_callback(uri, patch, mycb)

        assert "invoked callback did not change the patch object, but returned True" in str(exception_info.value)

    def test_no_change(self, co3_args):
        client = self._connect(co3_args)

        inc = self._create_incident(client, {"name": "test"})

        uri = "/incidents/%d" % inc['id']

        # Create a conflict
        inc["name"] = "the wrong value"
        inc["vers"] -= 1 # Force it to check old_value

        patch = resilient.Patch(inc)

        patch.add_value("name", "test updated")

        def mycb(response, patch_status, patch):
            raise resilient.NoChange

        response = client.patch_with_callback(uri, patch, mycb)

        assert response
        assert response.status_code == 200

        patch_status = resilient.PatchStatus(response.json())

        assert not patch_status.is_success()
        assert patch_status.get_conflict_fields() == ["name"]

    def test_conflict_with_handler(self, co3_args):
        client = self._connect(co3_args)

        inc = self._create_incident(client, {"name": "test"})

        uri = "/incidents/%d" % inc['id']

        # Create a conflict
        inc["name"] = "the wrong value"
        inc["vers"] -= 1 # Force it to check old_value

        patch = resilient.Patch(inc)

        patch.add_value("name", "test updated")

        def mycb(response, patch_status, patch):
            patch.exchange_conflicting_value(patch_status, "name", "test updated take 2")

        response = client.patch_with_callback(uri, patch, mycb)

        assert response
        assert response.status_code == 200

        assert "test updated take 2" == client.get(uri)["name"]

    def test_delete(self, co3_args):
        client = self._connect(co3_args)

        inc = self._create_incident(client, {"name": "test"})

        uri = "/incidents/%d" % inc['id']

        response = client.delete(uri)
        assert response
        assert response['success'] == True

    def test_post_attachment(self, co3_args):
        client = self._connect(co3_args)

        inc = self._create_incident(client, {"name": "test for attachment"})

        file_name = "test-for-attachment.txt"
        file_content = "this is test data"

        # Create the file
        temp_file = open(file_name, "w")
        temp_file.write(file_content)
        temp_file.close()
        # Post file to Resilient
        response = client.post_attachment("/incidents/{0}/attachments".format(inc["id"]),
                                          file_name,
                                          file_name,
                                          mimetype="text/plain")

        assert response
        assert response['name'] == file_name

        os.remove(file_name)

    def test_post_attachment_artifact(self, co3_args):
        client = self._connect(co3_args)

        inc = self._create_incident(client, {"name": "test for artifact attachment"})

        file_name = "test-for-attachment_artifact.txt"
        file_content = "this is test data"

        # Create the file
        temp_file = open(file_name, "w")
        temp_file.write(file_content)
        temp_file.close()
        # Post file to Resilient
        attachment_uri = "/incidents/{0}/artifacts/files".format(inc["id"])

        response = client.post_artifact_file(attachment_uri,
                                             artifact_type=16,
                                             artifact_filepath=file_name,
                                             description="Description",
                                             value=file_name)

        assert response

        os.remove(file_name)

    def test_get_config_file(self, co3_args):
        config_file = resilient.get_config_file("~/.resilient/app.config")

        assert config_file

    def test_get_client(self, co3_args):
        client = resilient.get_client(co3_args)

        assert client

    def test_throw_simple_http_exception(self, co3_args):
        with pytest.raises(resilient.SimpleHTTPException) as exception_info:
            client = resilient.SimpleClient("Not A real Org")
            user_info = client.connect("not_a_user@mail.com", "test")

            assert exception_info

    def test_get_const(self, co3_args):
        client = self._connect(co3_args)

        response = client.get_const()

        assert response

    def test_get_content(self, co3_args):
        client = self._connect(co3_args)

        response = client.get_content("/incidents")

        assert response

    def test_get_proxy_dict(self, co3_args):
        proxy_opts = type('', (), {})()
        proxy_opts.proxy_host = "http://resilientproxy.com"
        proxy_opts.proxy_port = "4443"
        proxy_opts.proxy_user = None
        proxy_opts.proxy_password = None
        proxy_dict = resilient.get_proxy_dict(proxy_opts)

        assert proxy_dict == {'https': 'http://resilientproxy.com:4443'}

        proxy_opts.proxy_user = "user"
        proxy_opts.proxy_password = "password"
        proxy_dict = resilient.get_proxy_dict(proxy_opts)

        assert proxy_dict == {'https': 'http://user:password@resilientproxy.com:4443/'}

        proxy_opts.proxy_host = "resilientproxy.com"

        proxy_dict = resilient.get_proxy_dict(proxy_opts)

        assert proxy_dict == {'https': 'https://user:password@resilientproxy.com:4443/'}

    def test_changing_description(self, co3_args):
        client = self._connect(co3_args)

        inc = self._create_incident(client, {"name": "Test Put and get_put"})
        # use PUT to change description
        inc["description"] = "Test Put method"
        uri = "/incidents/{}".format(inc["id"])
        inc = client.put(uri, inc)

        # use get_put to change description

        def change_description(json_data):
            json_data["description"] = json_data.get("description") + ", test get_put method"

        inc = client.get_put(uri, change_description)

        # Test no change error

        def no_change(json_data):
            raise resilient.NoChange

        inc = client.get_put(uri, no_change)

    @patch('resilient.SimpleClient.connect')
    @patch('resilient.SimpleClient.get')
    def test_get_client_dict(self, mock_get, mock_connect, co3_args):
        mock_connect.return_value = {"orgs": [{"id": 204}]}
        mock_get.return_value = {"actions_framework_enabled": True}

        args = {
            'host': 'resilient_host',
            'email': 'a@example.com',
            'password': 'password',
            'org': 'org',
        }

        rest_client = resilient.get_client(args)
        assert not rest_client.proxies

        #
        args['proxy_host'] = 'proxy_host'
        args['proxy_port'] = 1443

        rest_client = resilient.get_client(args)
        assert rest_client.proxies
        assert rest_client.proxies['https'] == "https://proxy_host:1443"

        #
        args['proxy_user'] = 'proxy_user'
        args['proxy_password'] = 'proxy_password'

        rest_client = resilient.get_client(args)
        assert rest_client.proxies
        assert rest_client.proxies['https'] == "https://proxy_user:proxy_password@proxy_host:1443/"

    @patch('resilient.SimpleClient.connect')
    @patch('resilient.SimpleClient.get')
    def test_get_client_namespace(self, mock_get, mock_connect, co3_args):
        mock_connect.return_value = {"orgs": [{"id": 204}]}
        mock_get.return_value = {"actions_framework_enabled": True}

        parser = ArgumentParser()
        parser.add_argument('--proxy_host')
        parser.add_argument('--proxy_port')
        parser.add_argument('--proxy_user')
        parser.add_argument('--proxy_password')
        parser.add_argument('--email')
        parser.add_argument('--password')
        parser.add_argument('--host')
        parser.add_argument('--org')

        #
        args = parser.parse_args([
            '--email', 'a@example.com',
            '--password', 'password',
            '--host', 'resilient_host',
            '--org', 'org'
        ])

        rest_client = resilient.get_client(args)
        assert not rest_client.proxies

        #
        args = parser.parse_args([
            '--email', 'a@example.com',
            '--password', 'password',
            '--host', 'resilient_host',
            '--org', 'org',
            '--proxy_host', 'proxy_host',
            '--proxy_port', '1443'
        ])

        rest_client = resilient.get_client(args)
        assert rest_client.proxies
        assert rest_client.proxies['https'] == "https://proxy_host:1443"

        #
        args = parser.parse_args([
            '--proxy_host', 'proxy_host',
            '--proxy_port', '1443',
            '--proxy_user', 'proxy_user',
            '--proxy_password', 'proxy_password',
            '--email', 'a@example.com',
            '--password', 'password',
            '--host', 'resilient_host',
            '--org', 'org'
        ])

        rest_client = resilient.get_client(args)
        assert rest_client.proxies
        assert rest_client.proxies['https'] == "https://proxy_user:proxy_password@proxy_host:1443/"


class TestGetConfig(object):

    @pytest.fixture(scope='session')
    def tmp_config_file(self, tmpdir_factory):
        tmp_config_dir = tmpdir_factory.mktemp(".resilient")
        tmp_config_file = os.path.expanduser(os.path.join(tmp_config_dir, DEFAULT_CONFIG_FILENAME))
        yield tmp_config_file
        rmtree(str(tmp_config_dir))

    def test_with_env_variable(self, monkeypatch, tmp_config_file):
        """
        Test with environment variable $APP_CONFIG_FILE.
        """
        monkeypatch.setenv("APP_CONFIG_FILE", str(tmp_config_file))
        result = resilient.get_config_file()
        assert result == tmp_config_file

    @patch('resilient.co3.os.path.exists', side_effect=mock_os_path_exists)
    def test_with_filename_exists_local(self, mock_os_path_exists):
        """
        Test with filename specified and not exists in home path.
        """
        test_file_name = "test_file"
        result = resilient.get_config_file(filename=test_file_name)
        assert result == test_file_name

    @patch('resilient.co3.os.path.exists', side_effect=mock_os_path_not_exists)
    def test_with_filename_not_exists_local(self, mock_os_path_not_exists):
        """
        Test with filename specified and exists in home path.
        """
        test_file_name = "test_file"
        test_file_abs = os.path.expanduser(os.path.join("~", ".resilient", test_file_name))
        result = resilient.get_config_file(filename=test_file_name)
        assert result == test_file_abs

    @patch('resilient.co3.os.path.exists', side_effect=mock_os_path_exists)
    def test_with_app_config_exists_local(self, mock_os_path_exists):
        """
        Test with default config specified and exists in home path.
        """
        result = resilient.get_config_file()
        assert result == DEFAULT_CONFIG_FILENAME

    @patch('resilient.co3.os.path.exists', side_effect=mock_os_path_not_exists)
    def test_with_app_config_not_exists_local(self, mock_os_path_not_exists):
        """
        Test with default config specified and not exists in home path.
        """
        result = resilient.get_config_file()
        assert result == DEFAULT_CONFIG_FILE