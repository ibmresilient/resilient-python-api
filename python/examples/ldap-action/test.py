# import objects and constants
from ldap3 import Server, Connection, SIMPLE, SYNC, ASYNC, SUBTREE, ALL, ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES, DEREF_ALWAYS
from ldap3.utils.conv import escape_bytes, format_json
import json

server = "ldap.forumsys.com"
port = 389
user = "cn=read-only-admin,dc=example,dc=com"
password = "password"

# ANONYMOUS, SIMPLE, SASL or NTLM
auth = SIMPLE
ssl = False

# Filter syntax see http://ldap3.readthedocs.org/searches.html#the-ldap-filter
bq = b'(objectClass=*)'
search_filter = bq # escape_bytes(bq)

value = "riemann"
search_filter = "(&(objectClass=person)(uid={}))".format(escape_bytes(value))
search_base = 'dc=example,dc=com'

# BASE, LEVEL or SUBTREE
search_scope = SUBTREE

# can be a restricted set e.g. ['sn', 'objectClass']
attribs = [ALL_ATTRIBUTES, ALL_OPERATIONAL_ATTRIBUTES]

# define the Server and the Connection objects
s = Server(server, port, get_info = ALL, use_ssl=ssl)  # define an unsecure LDAP server, requesting info on the server and the schema
with Connection(s, auto_bind = True,
                   client_strategy = SYNC,
                   user=user, password=password, authentication=auth, check_names=True) \
                   as c:

    print(s.info) # display info from the server. OID are decoded when recognized by the library

    # request a few objects from the LDAP server
    c.search(search_base, search_filter, search_scope,
                dereference_aliases=DEREF_ALWAYS,
                attributes = ALL_ATTRIBUTES,
                get_operational_attributes=True)
    response = c.response
    result = c.result
    # print(result)

    print(json.dumps(json.loads(c.response_to_json())["entries"]))
    for r in response:
        print(r['dn'], r['attributes'])  # return formatted attributes
        # print(r['dn'], r['raw_attributes'])  # return raw (bytes) attributes

    for e in c.entries:
        print(e.entry_get_dn())
        print(e.entry_to_json())
