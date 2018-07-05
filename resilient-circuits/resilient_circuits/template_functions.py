#!/usr/bin/env python
# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010, 2018. All Rights Reserved.

"""Template processing"""

# Jinja template functions

from __future__ import print_function
import sys
import jinja2
import json
import pprint
import logging
import time
import calendar
import datetime
import pytz
import random
import re

try:
    # Python 3.2 adds html.escape() and deprecates cgi.escape().
    from html import escape as html_escape
except ImportError:
    from cgi import escape as html_escape

try:
    # Python 3.x
    from base64 import encodebytes as b64encode
except ImportError:
    from base64 import encodestring as b64encode

import urllib

LOG = logging.getLogger(__name__)


def js_filter(val):
    """Jinja2 filter function 'js' produces JSONified string of the value, without surrounding quotes"""
    if val is None or isinstance(val, jinja2.Undefined):
        return "null"
    js = json_filter(val)
    return js[1:-1]


def json_filter(val, indent=0):
    """Jinja2 filter function 'json' produces JSONified string of the value"""
    if val is None or isinstance(val, jinja2.Undefined):
        return "null"
    return json.dumps(val, indent=indent, sort_keys=True)


def html_filter(val):
    """Jinja2 filter function 'html' produces HTML-encoded string of the value"""
    if isinstance(val, jinja2.Undefined):
        return "[undefined]"
    return html_escape(val)


def url_filter(val):
    """Jinja2 filter function 'url' produces URL-encoded string of the value"""
    if isinstance(val, jinja2.Undefined):
        return "[undefined]"
    return urllib.quote(str(val))


def idna_filter(val):
    """Jinja2 filter function 'idna' encodes the value per RFC 3490"""
    if isinstance(val, jinja2.Undefined):
        return "[undefined]"
    return val.encode("idna").decode("utf-8")


def punycode_filter(val):
    """Jinja2 filter function 'punycode' encodes the value per RFC 3492"""
    if isinstance(val, jinja2.Undefined):
        return "[undefined]"
    return val.encode("punycode").decode("utf-8")


def ldap_filter(val):
    """Jinja2 filter function 'ldap' produces LDAP-encoded string of the value"""
    if isinstance(val, jinja2.Undefined):
        return "[undefined]"
    escaped = []
    for char in str(val):
        if char < '0' or char > 'z' or char in "\\*()":
            char = "\\%02x" % ord(char)
        escaped.append(char)
    return ''.join(escaped)


def ps_filter(val):
    """Jinja2 filter function 'ps' escapes for use in a PowerShell commandline"""
    if isinstance(val, jinja2.Undefined):
        return "[undefined]"
    escaped = []
    for char in str(val):
        if char in "`$#'\"":
            char = "`" + char
        elif char == '\0':
            char = "`0"
        elif char == '\a':
            char = "`a"
        elif char == '\b':
            char = "`b"
        elif char == '\f':
            char = "`f"
        elif char == '\n':
            char = "`n"
        elif char == '\r':
            char = "`r"
        elif char == '\t':
            char = "`t"
        elif char == '\v':
            char = "`v"
        escaped.append(char)
    return ''.join(escaped)


def sh_filter(val):
    """Jinja2 filter function 'sh' escapes for use in a Unix shell commandline"""
    if isinstance(val, jinja2.Undefined):
        return "[undefined]"
    escaped = []
    for char in str(val):
        if char in "$#\"":
            char = "\\" + char
        elif ord(char) < 32 or ord(char) > 126:
            char = "\\%03o" % ord(char)
        escaped.append(char)
    return ''.join(escaped)


def pretty_filter(val, indent=2):
    """Jinja2 filter function 'pretty' produces pretty-printed string of the value"""
    if isinstance(val, jinja2.Undefined):
        return "[undefined]"

    def nice_repr(object, context, maxlevels, level):
        if sys.version_info.major < 3:
            typ = type(object)
            if typ is unicode:
                object = object.encode("utf-8")
        return pprint._safe_repr(object, context, maxlevels, level)

    printer = pprint.PrettyPrinter(indent=indent)
    printer.format = nice_repr
    return printer.pformat(val)


def iso8601(val):
    """Assuming val is an epoch milliseconds timestamp, produce ISO8601 datetime"""
    dt = datetime.datetime.utcfromtimestamp(int(int(val)/1000))
    return pytz.UTC.localize(dt).isoformat()


def timestamp(val):
    """Try convert non-timestamp values to a timestamp

       >>> timestamp({"year": 2018, "month": 8, "day": 1, "timezoneID": "CET"})
       1533078000000

       >>> timestamp(jinja2.Undefined())
       'null'

       >>> timestamp("now") > 1530000000000
       True

       >>> timestamp("now") > 2000000000000 # 2033
       False
    """
    if isinstance(val, dict):
        y = val.get("year", 1970)
        m = val.get("month", 1)
        d = val.get("day", 1)
        h = val.get("hour", 0)
        n = val.get("minute", 0)
        s = val.get("second", 0)
        u = val.get("milliSecond", 0)
        z = pytz.timezone(val.get("timezoneID", "UTC"))
        dt = datetime.datetime(y, m, d, h, n, s, u, z)
        return int(calendar.timegm(dt.utctimetuple()) * 1000)
    if isinstance(val, jinja2.Undefined):
        return "null"
    if isinstance(val, datetime.datetime):
        return int(calendar.timegm(val.utctimetuple()) * 1000)
    if val == "now":
        return int(calendar.timegm(datetime.datetime.now().utctimetuple()) * 1000)
    return val


def uniq(val, key=None):
    """Produce the unique list.  If val is a dict, produce unique of key values.

       >>> sorted(uniq([1,2,3,2]))
       [1, 2, 3]

       >>> sorted(uniq([ {"a":1}, {"a":2}, {"a":3}, {"a":2}]))
       [{'a': 1}, {'a': 2}, {'a': 3}]

       >>> sorted(uniq([ {"a":1}, {"a":2}, {"a":3}, {"a":2}, Exception()], "a"))
       [{'a': 1}, {'a': 2}, {'a': 3}, Exception()]
    """
    if not isinstance(val, list):
        return val
    if key is None:
        try:
            return list(set(val))
        except TypeError:
            pass
    keys = []
    values = []
    for value in val:
        try:
            thiskey = value[key]
        except:
            thiskey = repr(value)
        if thiskey not in keys:
            keys.append(thiskey)
            values.append(value)
    return values


def sample_filter(val, count=None):
    """Return a random sample from a list"""
    if count is None:
        # Return a single value
        try:
            return random.sample(list(val), 1)[0]
        except ValueError:
            return None
    else:
        # Return a list
        try:
            return random.sample(list(val), count)
        except ValueError:
            return []


def camel_filter(val):
    """Return CamelCase

       >>> camel_filter("a#bc_def")
       'ABcDef'
    """
    titlecase = val.title()
    return re.sub(r"[\W^_]", "", titlecase)


def base64_filter(val, indent=2):
    """Jinja2 filter function 'base64' breaks text into fixed-width blocks"""
    if isinstance(val, jinja2.Undefined):
        return ""
    s = json.dumps(val).encode("utf-8")
    return b64encode(s).decode("utf-8")


JINJA_FILTERS = {"json": json_filter,
                 "js": js_filter,
                 "html": html_filter,
                 "url": url_filter,
                 "idna": idna_filter,
                 "punycode": punycode_filter,
                 "ldap": ldap_filter,
                 "ps": ps_filter,
                 "sh": sh_filter,
                 "pretty": pretty_filter,
                 "timestamp": timestamp,
                 "iso8601": iso8601,
                 "uniq": uniq,
                 "sample": sample_filter,
                 "camel": camel_filter,
                 "base64": base64_filter}


# Maintain one global Environment
ENV = jinja2.Environment(autoescape=jinja2.select_autoescape(default_for_string=False))
ENV.globals.update(JINJA_FILTERS)
ENV.filters.update(JINJA_FILTERS)


def render(template, data):
    """Render data into a template, producing a string result

        The template is usually a string, but can be a dict.

        >>> render("template {{value}}", {"value":"123"})
        u'template 123'

        >>> render({"template": "{{value}}"}, {"value":"123"})
        u'{"template": "123"}'

        You can escape values using the 'json' filter,
        or the 'url' or 'html' or 'ldap' filters.

        >>> render('{"template": {{value|json}} }', {"value":'1"23'})
        u'{"template": "1\\\\"23" }'

        >>> render('{"template": "{{value|js}}" }', {"value":'1"23'})
        u'{"template": "1\\\\"23" }'

        >>> render('{"template": {{value|ldap}} }', {"value":'1*23'})
        u'{"template": 1\\\\2a23 }'

        >>> render('shell "{{value|ps}}"', {"value":'$"foo"'})
        u'shell "`$`"foo`""'

        >>> render('shell "{{value|sh}}"', {"value":'$"foo"'})
        u'shell "\\\\$\\\\"foo\\\\""'

        >>> render('template={{value|timestamp}}', {"value":0})
        u'template=0'

        >>> render('template={{value|timestamp}}', {})
        u'template=null'

        >>> render('template={{value|timestamp}}', {"value":{"year":2015, "month":7, "day":15}})
        u'template=1436918400000'

        >>> render('template={{value|timestamp}}', {"value":datetime.datetime(2015, 7, 15)})
        u'template=1436918400000'

        >>> d = json.loads('{"attributes": \
                {"cn": ["Albert Einstein"], "createTimestamp": "2014-02-21 16:51:33+00:00", \
                 "creatorsName": "cn=admin,dc=example,dc=com", \
                 "entryCSN": ["20150720185447.990131Z#000000#000#000000"], \
                 "entryDN": "uid=einstein,dc=example,dc=com", \
                 "entryUUID": "29f6dc28-2f64-1033-898b-a53eb149a944", \
                 "hasSubordinates": false, \
                 "mail": ["einstein@ldap.forumsys.com"], \
                 "modifiersName": "cn=admin,dc=example,dc=com", \
                 "modifyTimestamp": "2015-07-20 18:54:47+00:00", \
                 "objectClass": ["inetOrgPerson", "organizationalPerson", "person", "top"], \
                 "sn": ["Einstein"], \
                 "structuralObjectClass": "inetOrgPerson", \
                 "subschemaSubentry": "cn=Subschema", \
                 "telephoneNumber": ["314-159-2653"], \
                 "uid": ["einstein"]}, \
                "dn": "uid=einstein,dc=example,dc=com"}')
        >>> render('{"description": "DN={{dn}}, mail={{attributes.mail[0]}}"}',d)
        u'{"description": "DN=uid=einstein,dc=example,dc=com, mail=einstein@ldap.forumsys.com"}'
    """

    stringtemplate = template
    if isinstance(template, dict):
        stringtemplate = json.dumps(template, sort_keys=True)

    try:
        jtemplate = ENV.from_string(stringtemplate)
    except jinja2.exceptions.TemplateSyntaxError:
        LOG.error("Render failed, with template: {0}".format(stringtemplate))
        raise

    try:
        stringvalue = jtemplate.render(data)
    except jinja2.exceptions.TemplateError:
        LOG.error("Render failed, with data: {0}".format(data))
        raise
    return stringvalue


def render_json(template, data):
    """Render data into a template, producing a JSON result
       Also clean up any "really bad" control characters to avoid failure.

       >>> d = {"value": "the" + chr(10) + "new" + chr(10) + "thing"}
       >>> render_json('{"result":"{{value}}"}', d)
       {u'result': u'the new thing'}

       >>> d = {"value": "the" + chr(1) + "new" + chr(9) + "thing"}
       >>> render_json('{"result":"{{value}}"}', d)
       {u'result': u'the new thing'}
    """
    result = render(template, data)
    for n in range(1, 32):
        result = result.replace(chr(n), " ")
    try:
        value = json.loads(result)
    except:
        LOG.info(result)
        raise
    return value


def environment():
    return ENV


def test(template):
    """Test some basic functionality

        The result is a string.  It's ok to not use any tags.
        >>> test("thing")
        u'thing'

        Tags return unescaped data
        >>> test("this is my {{number}}")
        u'this is my 42'
        >>> test("this is my {{string}}")
        u'this is my templates'

        The 'json' filter return JSON-quoted result,
        >>> test("this is my {{number|json}}")
        u'this is my 42'
        >>> test("this is my {{string|json}}")
        u'this is my "templates"'

        Dotted forms can navigate the tree of data,
        >>> test("object.name is {{object.name}}")
        u'object.name is v<a>lue'

        To render HTML, use the 'html' filter,
        >>> test( {"text":"<div>{{object.name|html}}</div>"} )
        u'{"text": "<div>v&lt;a&gt;lue</div>"}'

        Test the 'iso8601' filter
        >>> test("Go back to {{epochdate|iso8601}}")
        u'Go back to 2002-05-02T01:47:30+00:00'

        The filters can also be used as global functions json(), html() etc,
        >>> test('{{html("f<oo")}}')
        u'f&lt;oo'

        Index by index,
        >>> test("number is {{numbers[1]}}")
        u'number is 2'

        Loop over collections,
        >>> test("numbers are {% for n in numbers%}{{n}},{% endfor %}")
        u'numbers are 1,2,3,'

        Built-in filters should "just work",
        >>> test("{{string|upper}}")
        u'TEMPLATES'

        >>> test("{{domain|idna}}")
        u'xn--c1yn36f'

        >>> test("{{domain|punycode}}")
        u'c1yn36f'

    """
    data = {"string": "templates",
            "number": 42,
            "numbers": [1, 2, 3],
            "object": {"name": "v<a>lue"},
            "epochdate": 1020304050607,
            "domain": u"\u9ede\u770b"}
    return unicode(render(template, data))


def main():
    """Just some tests or usage statement"""
    import sys
    if len(sys.argv) > 1:
        test_template = sys.argv[1]
    else:
        import doctest
        doctest.testmod()
        test_template = {"usage": "Use {{string}} in json, or {{string|json}} within strings"}
    print(test_template)
    print(test(test_template))


if __name__ == "__main__":
    main()
