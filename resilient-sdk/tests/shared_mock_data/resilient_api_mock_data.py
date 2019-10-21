#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2019. All Rights Reserved.

SESSION_DATA = {
    "session_ip": "192.168.56.1",
    "user_fname": "Orchestration",
    "user_email": "integrations@example.com",
    "saml_alias": None,
    "csrf_token": "79945884c2e6f2339cbffbbaba01f17b",
    "user_lname": "Engine",
    "user_id": 1,
    "is_ldap": False,
    "is_saml": False,
    "orgs": [{
        "city": "AnyCity",
        "addr": None,
        "zip": None,
        "has_available_twofactor": False,
        "perms": {"create_shared_layout": True, "administrator": False, "create_incs": True, "master_administrator": True, "observer": False},
        "supports_ldap": False,
        "enabled": True,
        "twofactor_auth_domain": None,
        "attachments_enabled": True,
        "has_saml": False,
        "state": None,
        "addr2": None,
        "twofactor_cookie_lifetime_secs": 0,
        "require_saml": False,
        "tasks_private": False,
        "authorized_ldap_group": None,
        "id": 201,
        "name": "Other Mock Org"
    }, {
        "city": None,
        "addr": None,
        "zip": None,
        "has_available_twofactor": False,
        "perms": {"create_shared_layout": True, "administrator": False, "create_incs": True, "master_administrator": True, "observer": False},
        "supports_ldap": False,
        "enabled": True,
        "twofactor_auth_domain": None,
        "attachments_enabled": True,
        "has_saml": False,
        "state": None,
        "addr2": None,
        "twofactor_cookie_lifetime_secs": 0,
        "require_saml": False,
        "tasks_private": False,
        "authorized_ldap_group": None,
        "id": 202,
        "name": "Test Organization"
    }]
}

ORG_DATA = {
    "actions_framework_enabled": True,
    "users": {
        "2": {
            "id": 2,
            "fname": "Orchestration",
            "lname": "Engine",
            "status": "A",
            "email": "integrations@example.com",
            "phone": None,
            "cell": None,
            "title": None,
            "notes": None,
            "locked": False,
            "enabled": True,
            "roles": {"administrator": False, "observer": False, "master_administrator": True, "create_incs": True},
            "last_login": 1475614308048,
            "org_id": 202,
            "group_ids": [],
            "is_external": False
        },
        "3": {
            "id": 3,
            "fname": "User",
            "lname": "Three",
            "status": "A",
            "email": "someone@example.com",
            "phone": None,
            "cell": None,
            "title": None,
            "notes": None,
            "locked": False,
            "enabled": True,
            "roles": {"administrator": False, "observer": False, "master_administrator": True, "create_incs": True },
            "last_login": 1476711664869,
            "org_id": 202,
            "group_ids": [],
            "is_external": False
        }
    }
}
