# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.
import pytest
import requests
import time
from resilient_lib.components import oauth2_client_credentials_session
from resilient_lib.components.oauth2_client_credentials_session import OAuth2ClientCredentialsSession


def mock_token_request_factory(elapsed_time=None, expires_in=None, status_code=None, token=None):
    return lambda *args, **kwargs: MockTokenRequest(elapsed_time=elapsed_time, expires_in=expires_in,
                                                    status_code=status_code, token=token)


def raise_error(*args, **kwargs):
    raise ValueError()


def return_values_each_call(it):
    class StoreAndReturnValue(object):
        """
        Create a generator from iterator, and act like a function, returning
        next value every time class is called.
        """
        def __init__(self, it):
            self.gen = (x for x in it)
            self.current = 0

        def __call__(self, *args, **kwargs):
            self.current += 1
            return next(self.gen)

    return StoreAndReturnValue(it)


class MockTokenRequest(object):
    class ElapsedTime(object):
        def __init__(self, elapsed_time):
            self.elapsed_time = elapsed_time

        def total_seconds(self):
            return self.elapsed_time

    def __init__(self, elapsed_time=None, expires_in=None, status_code=None, token=None):
        self.status_code = status_code if status_code is not None else 200
        self.return_json = {
            "access_token": "token" if token is None else token
        }

        if elapsed_time is None:
            elapsed_time = 3
        self.elapsed = self.ElapsedTime(elapsed_time)

        if expires_in is not None:
            self.return_json["expires_in"] = expires_in

    def json(self):
        return self.return_json

    def raise_for_status(self):
        if self.status_code > 299:
            raise ValueError()


class TestAuthenticator(object):
    @pytest.fixture(autouse=True)
    def clean_up_singletons(self):
        if OAuth2ClientCredentialsSession.__dict__.get("__it__", None) is not None:
            del OAuth2ClientCredentialsSession.__it__

    def test_multiple_sessions_multiple_tokens(self, monkeypatch):
        monkeypatch.setattr(requests.sessions.Session, 'post', mock_token_request_factory(token="api1"))
        api1 = OAuth2ClientCredentialsSession("url:example1", "s", "t")
        monkeypatch.setattr(requests.sessions.Session, 'post', mock_token_request_factory(token="api2"))
        api2 = OAuth2ClientCredentialsSession("url:example2", "s", "t")

        assert api1.access_token == "api1"
        assert api2.access_token == "api2"

    def test_creates_session_with_passing_authentication(self, monkeypatch):
        monkeypatch.setattr(requests.sessions.Session, 'post', mock_token_request_factory())
        auth = OAuth2ClientCredentialsSession("test", "test", "test")
        assert getattr(auth, 'access_token', None) is not None

    def test_fails_to_create_session_with_bad_authentication(self, monkeypatch):
        monkeypatch.setattr(requests.sessions.Session, 'post', mock_token_request_factory(status_code=403))
        with pytest.raises(ValueError):
            OAuth2ClientCredentialsSession("test", "test", "test")

    def test_authenticator_fails_without_required_fields(self, monkeypatch):
        monkeypatch.setattr(OAuth2ClientCredentialsSession, 'authenticate', lambda *_: True)
        with pytest.raises(ValueError):
            OAuth2ClientCredentialsSession(None, None, None)
        with pytest.raises(ValueError):
            OAuth2ClientCredentialsSession(None, "s", "t")
        with pytest.raises(ValueError):
            OAuth2ClientCredentialsSession("t", None, "t")
        with pytest.raises(ValueError):
            OAuth2ClientCredentialsSession("t", "s", None)

    def test_scope_gets_passed_when_given(self, monkeypatch):
        def confirm_scope_data(*args, **kwargs):
            data = kwargs.pop("data", None)  # instead of data in signature because of 2.7
            assert data is not None
            assert data['scope'] is not None
            return mock_token_request_factory()()

        monkeypatch.setattr(requests.sessions.Session, 'post', confirm_scope_data)
        OAuth2ClientCredentialsSession("test", "test", "test", scope=["scope"])

    def test_no_expiration_doesnt_fail(self, monkeypatch):
        monkeypatch.setattr(requests.sessions.Session, 'post', mock_token_request_factory())
        auth = OAuth2ClientCredentialsSession("test", "test", "test")
        assert auth.expiration_time is None
        assert getattr(auth, 'access_token', None) is not None

    def test_expiration_time_is_set(self, monkeypatch):
        monkeypatch.setattr(requests.sessions.Session, 'post', mock_token_request_factory(expires_in=50))
        auth = OAuth2ClientCredentialsSession("test", "test", "test")
        assert auth.expiration_time is not None

    def test_updating_token_after_expiration(self, monkeypatch):
        monkeypatch.setattr(requests.sessions.Session, 'post', mock_token_request_factory(expires_in=50))
        monkeypatch.setattr(OAuth2ClientCredentialsSession, 'update_token', raise_error)
        auth = OAuth2ClientCredentialsSession("test", "test", "test")
        auth.expiration_time = time.time() - 1

        with pytest.raises(ValueError):
            auth.get("https://www.ibm.com")

    def test_detect_updating_token_after_request_ends_after_expiration(self, monkeypatch):
        """
        Test that when a request is made while the token is not expired, but the request fails,
        if sending the request was long enough where token might have expired, that the token will get refreshed,
        and the request will be made again.

        monkeypatch 'post', because authentication uses POST request
        monkey patch module's import of time, because pytest also uses time, to create the conditions
        where token expired during the duration of request being made.
        """
        monkeypatch.setattr(requests.sessions.Session, 'post',
                            mock_token_request_factory(expires_in=10, elapsed_time=0))
        monkeypatch.setattr(oauth2_client_credentials_session.time, 'time',
                            return_values_each_call([time.time(), time.time(), time.time() + 15]))
        monkeypatch.setattr(requests.sessions.Session, 'request',
                            mock_token_request_factory(status_code=401, elapsed_time=20))
        monkeypatch.setattr(OAuth2ClientCredentialsSession, 'update_token', raise_error)

        auth = OAuth2ClientCredentialsSession("test", "test", "test")

        with pytest.raises(ValueError):
            auth.get("https://www.ibm.com")
