#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2023. All Rights Reserved.

import logging

from resilient_app_config_plugins.constants import (
    PAM_SECRET_PREFIX, PAM_SECRET_PREFIX_WITH_BRACKET)
from resilient_app_config_plugins.plugin_base import PAMPluginInterface
from six import string_types
from six.moves import UserDict

from resilient import constants, helpers

LOG = logging.getLogger(__name__)

class ConfigDict(dict):
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

    def get(self, config_key, default=None):
        """
        Read key from data.
        If found in data, decrypt using the stored token, key pair.
        If not found, then should be looked for in ENV

        :param config_key: key to retrieve value of
        :type config_key: str
        :return: secret value of config_key either decrypted from protected secret or from ENV
        :rtype: str
        """
        if not config_key:
            return default

        config_key = config_key.lstrip(constants.PROTECTED_SECRET_PREFIX)

        if config_key in self.data:
            tkn, key = self.data.get(config_key)

            protected_secret = helpers.decrypt_protected_secret(tkn, key, config_key)
            protected_secret = protected_secret if protected_secret else helpers.get_config_from_env(config_key, default)
        else:
            protected_secret = helpers.get_config_from_env(config_key, default)

        return protected_secret

class AppConfigManager(UserDict, ConfigDict):
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

    def __init__(self, dict={}, pam_plugin_type=None, key="_"):
        UserDict.__init__(self, dict) # need to use old-style super for Python 2

        if pam_plugin_type:
            if not issubclass(pam_plugin_type, PAMPluginInterface):
                raise ValueError("'pam_plugin_type' must be a subclass of 'PAMPluginInterface'")
            self.pam_plugin = pam_plugin_type(protected_secrets_manager=AppConfigManager.protected_secrets_manager, key=key)
        else:
            self.pam_plugin = None

        self._convert_sub_dicts_to_obj(pam_plugin_type)

    ########################################
    ##### superclass 'dict' overrides ######
    ########################################

    def get(self, key, default=None):
        # must override the default 'get' because we need it to use the
        # custom '__getitem__' which will use the PAM logic when necessary
        try:
            return self[key]
        except KeyError:
            return default

    def __repr__(self):
        # overriding the default '__repr__' will allow
        # for hiding the credentials that are meant to be hidden
        data = {}
        for key in self.data:
            # have to bypass this class' logic which incorporates
            # pam and protected secret substitution
            data[key] = self.data[key]
        return str(data)

    def __reduce__(self):
        """Return state information for pickling"""
        inst_dict = vars(self).copy()
        return self.__class__, (), inst_dict or None, None, iter(self.data.items())

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
        item = UserDict.__getitem__(self, key)

        # NOTE: the order of these checks is important -- the check for the version
        # with bracket has to be checked first, as otherwise the bracket won't be
        # removed from the item
        # also NOTE: there can be a mix of ^{} and ${} items in the secret or any
        # number of {} secrets in the configs

        # handle protected secrets
        if isinstance(item, string_types) and constants.PROTECTED_SECRET_PREFIX_WITH_BRACKET in item:
            item = self.replace_secret_in_config(item, AppConfigManager.protected_secrets_manager, constants.PROTECTED_SECRET_PREFIX_WITH_BRACKET)
        elif isinstance(item, string_types) and item.startswith(constants.PROTECTED_SECRET_PREFIX):
            item = self.replace_secret_in_config(item, AppConfigManager.protected_secrets_manager, constants.PROTECTED_SECRET_PREFIX)

        # handle pam plugin secrets
        if self.pam_plugin and isinstance(item, string_types) and PAM_SECRET_PREFIX_WITH_BRACKET in item:
            item = self.replace_secret_in_config(item, self.pam_plugin, PAM_SECRET_PREFIX_WITH_BRACKET)
        elif self.pam_plugin and isinstance(item, string_types) and item.startswith(PAM_SECRET_PREFIX):
            item = self.replace_secret_in_config(item, self.pam_plugin, PAM_SECRET_PREFIX)

        return item

    def _convert_sub_dicts_to_obj(self, plugin_type):
        """
        Recursively create AppConfigManagers for any sub-dictionaries of the top-level
        dict. Using the underlying dict (which is iterable via ``self``), we can
        iterate over the data of the underlying dictionary.

        Plugin type is not persisted for the whole AppConfigManager class -- thus it
        must be provided here to propagate to sub-dictionaries.

        :param plugin_type: plugin type for the app config manager
        :type plugin_type: ``resilient_app_config_plugins.plugin_base.PAMPluginInterface``
        """
        for key in self.data:
            if isinstance(self.data[key], dict) or isinstance(self.data[key], AppConfigManager):
                # for deeper levels of dictionaries, pass through their "key"
                # so that future uses might maintain that information
                self.data[key] = AppConfigManager(dict=self.data[key], pam_plugin_type=plugin_type, key=key)

    def _asdict(self):
        """
        This method is needed to maintain backwards compatibility with
        the way that AppFunctionComponent.app_configs used to work.

        :return: simply returns itself as AppConfigs behave like namedtuples and dicts
        :rtype: AppConfig
        """
        return self

    def update(self, mapping=(), **kwargs):
        UserDict.update(self, mapping, **kwargs)
        ConfigDict.update(self, mapping, **kwargs)

    @staticmethod
    def replace_secret_in_config(item, secret_manager, secret_prefix):
        """
        Use either protected secrets or app config plugin to substitute
        in values where appropriate for item from app.config

        The method here is mostly required to support having multiple
        secrets in a config. This method deals with multiple substitutions
        and, in conjunction with the logic in __getitem__, will substitute
        all secrets in a config.

        To have multiple secrets in a config, brackets must be used.

        **Example:**

        Assuming that you have protected secrets TABLE_SECRET_NAME
        and VALUE_SECRET_NAME, a sql query could be constructed in
        an app.config like this:

        .. code-block::

            [fn_my_app]
            sql_query=FROM ${TABLE_SECRET_NAME} select ${VALUE_SECRET_NAME};

        :param item: value from app.config
        :type item: str
        :param secret_manager: Protected Secrets Manager or App Config Plugin
        :type secret_manager: ProtectedSecretsManager|PAMPluginInterface
        :param secret_prefix: "$" or "${" or "^" or "^{"
        :type secret_prefix: str
        :return: substituted value of app.config item
        :rtype: str
        """
        original_item = item
        if secret_prefix not in item:
            return item
        start = item.index(secret_prefix)

        # loop through any prefixed values in the item and substitute them
        # the loop here is required for multiple values in a line
        while start < len(item):
            end = item.index("}", start) if "}" in item[start:] else len(item)
            prefixed_item = item[start:end+1]
            unprefixed_item = prefixed_item.replace(secret_prefix, "").replace("}", "")
            secret_value = secret_manager.get(unprefixed_item, prefixed_item)

            # since we set prefixed_item to be the default value that will
            # be returned when no value is found, log a warning telling the
            # user that their value wasn't found
            if secret_value == prefixed_item:
                manager_type_str = "PAM Plugin" if isinstance(secret_manager, PAMPluginInterface) else "Protected Secrets"
                LOG.debug("Failed to find a secret in %s. To properly deploy your app, please make sure that the secret is correctly configured",
                          manager_type_str)
            else:
                LOG.debug("Value found for %s", original_item)

            item = u"{0}{1}{2}".format(item[0:start], secret_value, item[end+1:])

            # restart the search from the one beyond where we just subbed in the found value
            length_secret = len(secret_value) if secret_value else 0
            start = item.index(secret_prefix, start+length_secret) if secret_prefix in item[start+length_secret:] else len(item)
        return item
