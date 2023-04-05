#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import logging

from resilient_app_config_plugins.plugin_base import PAMPluginInterface
from resilient_app_config_plugins.constants import PAM_SECRET_PREFIX
from six import string_types
from six.moves import UserDict

from resilient import constants, helpers

LOG = logging.getLogger(__name__)

class ConfigDict(UserDict, dict):
    """A dictionary, with property-based accessor

    >>> opts = {"one": 1}
    >>> cd = ConfigDict(opts)
    >>> cd["one"]
    1
    >>> cd.one
    1

    """
    def __getattr__(self, name):
        """Attributes are made accessible as properties"""
        try:
            return self[name]
        except KeyError:
            raise AttributeError()

class ProtectedSecretsManager:
    """
    Class to manage all protected secrets and env variables.
    Works with existing protected secrets logic introduced in v47.0.

    If running in integration server, only allows for use of ENV variables
    """

    def __init__(self, path_secrets_dir=constants.PATH_SECRETS_DIR, path_jwk_file=constants.PATH_JWK_FILE):
        self.data = {}

        # find all protected secrets in the PATH_SECRETS_DIR folder
        # and retain the decryption key and encrypted value in self.data
        if helpers.is_running_in_app_host(constants.ENV_VAR_APP_HOST_CONTAINER):
            for config_key in helpers.get_protected_secrets_keys(path_secrets_dir):
                if helpers.protected_secret_exists(config_key, path_secrets_dir, path_jwk_file):
                    # protected secrets are stored as tuple of token, key
                    self.data[config_key] = helpers.get_protected_secret_token_and_key(config_key, path_secrets_dir, path_jwk_file)

    def get(self, config_key):
        """
        Read key from data.
        If found in data, decrypt using the stored token, key pair.
        If not found, then should be looked for in ENV

        :param config_key: key to retrieve value of
        :type config_key: str
        :return: secret value of config_key either decrypted from protected secret or from ENV
        :rtype: str
        """

        config_key = config_key.lstrip(constants.PROTECTED_SECRET_PREFIX)

        if config_key in self.data:
            tkn, key = self.data.get(config_key)

            protected_secret = helpers.decrypt_protected_secret(tkn, key, config_key)
            protected_secret = protected_secret if protected_secret else helpers.get_config_from_env(config_key)
        else:
            protected_secret = helpers.get_config_from_env(config_key)

        return protected_secret

class AppConfigManager(ConfigDict):
    """
    Intermediary to manage plain-text configs, $-prefixed protected secrets/env vars,
    and ^-prefixed PAM secrets.

    The AppConfigManager class manages all of those, with late-binding using the
    __getattr__ method to govern when data is retrieved from sensitive locations.

    A ProtectedSecretManager is required to manage all protected secrets and a
    PAM plugin *should* be provided to manage externally managed credentials.
    If no plugin is provided, plain text values will be returned for ^.

    :param dict: initial dictionary, defaults to None
    :type dict: dict, optional
    :param pam_plugin_type: PAM plugin to manage external credentials, defaults to None
    :type pam_plugin_type: ``resilient_app_config_plugins.plugin_base.PAMPluginInterface``, optional
    """

    # static protected secrets manager variable
    # used for pulling protected secrets here and in
    # any plugins that need access to protected secrets
    protected_secrets_manager = ProtectedSecretsManager()

    def __init__(self, dict=None, pam_plugin_type=None, key="_"):
        super(AppConfigManager, self).__init__(dict)

        if pam_plugin_type:
            assert issubclass(pam_plugin_type, PAMPluginInterface), "'pam_plugin_type' must be a subclass of 'PAMPluginInterface'"
            self.pam_plugin = pam_plugin_type(protected_secrets_manager=AppConfigManager.protected_secrets_manager, key=key)
        else:
            self.pam_plugin = None

        self._convert_sub_dicts_to_obj(pam_plugin_type)

    def __getitem__(self, key):
        """
        This is the key part -- overwrite the behavior of the dictionary
        for retrieving items. The dictionary's item is retrieved. This item
        may or may not start with a protected prefix. If it does, use either the
        protected secrets manager or the pam secrets manager is to resolve the
        item that is to be returned

        NOTE: either ``get()`` methods called here could throw errors. That is
        by design that we don't trap them as we want those managers themselves to
        be able to communicate to the original caller of this method.

        :param key: key to search for in the underlying dict
        :type key: object
        :return: item from the dictionary, protected secret, or the pam plugin
        """
        item = super(AppConfigManager, self).__getitem__(key)
        if isinstance(item, string_types) and item.startswith(constants.PROTECTED_SECRET_PREFIX):
            item = AppConfigManager.protected_secrets_manager.get(item)
        elif self.pam_plugin and isinstance(item, string_types) and item.startswith(PAM_SECRET_PREFIX):
            item = self.pam_plugin.get(item)

        return item

    def _convert_sub_dicts_to_obj(self, plugin_type):
        """
        Recursively create AppConfigManagers for any sub-dictionaries of the top-level
        data. Using the ``data`` object exposed by the ``UserDict`` class, we can
        iterate over the data of the underlying dictionary.

        Plugin type is not persisted for the whole AppConfigManager class -- thus it
        must be provided here to propogate to sub-dictionaries.

        :param plugin_type: plugin type for the app config manager
        :type plugin_type: ``resilient_app_config_plugins.plugin_base.PAMPluginInterface``
        """
        for key in self.data:
            if isinstance(self.data[key], dict):
                # for deeper levels of dictionaries, pass through their "key"
                # so that future uses might maintain that information
                self.data[key] = AppConfigManager(dict=self.data[key], pam_plugin_type=plugin_type, key=key)

    def _asdict(self):
        """
        This method is needed to maintain backwards compatability with
        the way that AppFunctionComponent.app_configs used to work.

        :return: simply returns itself as AppConfigs behave like namedtuples and dicts
        :rtype: AppConfig
        """
        return self
