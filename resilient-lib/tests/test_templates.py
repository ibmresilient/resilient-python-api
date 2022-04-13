import datetime
import os

import jinja2
import pytest
from resilient_lib import (global_jinja_env, make_payload_from_template,
                           render, render_json)
from resilient_lib.components.templates_common import (soar_datetimeformat,
                                                       soar_splitpart,
                                                       soar_substitute,
                                                       soar_trimlist)

TEST_DATA = data = {
    "string": "templates",
    "number": 42,
    "numbers": [1, 2, 3],
    "value_list": [' a', ' b', ' c ', 'd'],
    "object": {"name": "v<a>lue"},
    "epochdate": 1020304050607,
    "utcdate": "2021-10-22T20:53:53.913Z",
    "iso8601": "2021-10-22T20:53:53+00:00",
    "domain": u"\u9ede\u770b",
    "url": "https://example.com:8080",
    "repeat_list1": [1, 2, 3, 2],
    "repeat_list2": [{"a": 1}, {"a": 2}, {"a": 3}, {"a": 2}],
    "norepeat_list3": [{"a": 1}, {"a": 2}, {"a": 3}, {"a": 4}],
    "json": {
        "something": 42,
        "something_else": [
            { "a": "aa"},
            { "b": "bb"}
        ]
    }
}

TEST_ATTRIBUTES = {
    "attributes": {
        "cn": ["Albert Einstein"],
        "createTimestamp": "2014-02-21 16:51:33+00:00",
        "creatorsName": "cn=admin,dc=example,dc=com",
        "entryCSN": ["20150720185447.990131Z#000000#000#000000"],
        "entryDN": "uid=einstein,dc=example,dc=com",
        "entryUUID": "29f6dc28-2f64-1033-898b-a53eb149a944",
        "hasSubordinates": False,
        "mail": ["einstein@ldap.forumsys.com"],
        "modifiersName": "cn=admin,dc=example,dc=com",
        "modifyTimestamp": "2015-07-20 18:54:47+00:00",
        "objectClass": ["inetOrgPerson", "organizationalPerson", "person", "top"],
        "sn": ["Einstein"],
        "structuralObjectClass": "inetOrgPerson",
        "subschemaSubentry": "cn=Subschema",
        "telephoneNumber": ["314-159-2653"],
        "uid": ["einstein"]
    },
    "dn": "uid=einstein,dc=example,dc=com"
}

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
TEST_OVERRIDE_TEMPLATE = os.path.join(CURRENT_DIR, "data/override_template.jinja")
TEST_DEFAULT_TEMPLATE = os.path.join(CURRENT_DIR, "data/default_template.jinja")

@pytest.mark.parametrize("template, expected_results", [
        ("thing", u"thing"),
        ("this is my {{number}}", u"this is my 42"),
        ("this is my {{string}}", u'this is my templates'),
        ("object.name is {{object.name}}", u"object.name is v<a>lue"),
        ("number is {{numbers[1]}}", u"number is 2"),
        ("numbers are {% for n in numbers%}{{n}}{% if not loop.last %},{% endif %}{% endfor %}", u"numbers are 1,2,3"),
    ])
def test_basic(template, expected_results):
    """Test some basic functionality

        Test the 'iso8601' filter
        assert test("Go back to {{epochdate|iso8601}}")
        u'Go back to 2002-05-02T01:47:30+00:00'
    """
    assert render(template, TEST_DATA) == expected_results

@pytest.mark.parametrize("template, expected_results", [
        ("{{string|upper}}", u'TEMPLATES'),
        ("{{string|replace('s', 'ss')}}", u'templatess'),
        ("{{numbers|last}}", '3')
    ])
def test_builtin_filters(template, expected_results):
    # make sure we still have access to built-in filters
    assert render(template, TEST_DATA) == expected_results

# todo maybe an error with default date_format
@pytest.mark.parametrize("template, expected_results", [
        ("{{utcdate|soar_datetimeformat(split_at='.')}}", "1634936033000"),
        ("{{iso8601|soar_datetimeformat(split_at='+', date_format='%Y-%m-%dT%H:%M:%S')}}", "1634936033000"),
        ("{{soar_datetimeformat('2002-05-02T01:47:30')}}", "1020304050000"),
        ("{{'1'|soar_substitute('{\"1\":\"Low\"}')}}", u"Low"),
        ("{{'2'|soar_substitute('{\"1\":\"Low\", \"DEFAULT\":\"High\"}')}}", u"High"),
        ("{{'abc - def'|soar_splitpart(1)}}", u"def"),
        ("{{'abc - def'|soar_splitpart(5)}}", u"abc - def"),
        ("{{'abc/def'|soar_splitpart(0, split_chars='/')}}", u"abc"),
        ("{{value_list|soar_trimlist}}", u"['a', 'b', 'c', 'd']"),
        ("{{object|js}}", '\n"name": "v<a>lue"\n'),
        ({"text":"<div>{{object.name|html}}</div>"}, u'{"text": "<div>v&lt;a&gt;lue</div>"}'),
        ("{{html('f<oo')}}", u'f&lt;oo'),
        ("{{url|url}}", 'https%3A//example.com%3A8080'),
        ("{{domain|idna}}", u'xn--c1yn36f'),
        ("{{domain|punycode}}", u'c1yn36f'),
        ("Go back to {{epochdate|iso8601}}", u'Go back to 2002-05-02T01:47:30+00:00'),
        ("{{repeat_list1|uniq}}", "[1, 2, 3]"),
        ('{{repeat_list2|uniq}}', "[{'a': 1}, {'a': 2}, {'a': 3}]"),
        ('{{norepeat_list3|uniq}}', "[{'a': 1}, {'a': 2}, {'a': 3}, {'a': 4}]"),
        ("this is my {{number|json}}", u"this is my 42"),
        ("this is my {{string|json}}", u'this is my "templates"'),
        ("{{string|base64}}", 'InRlbXBsYXRlcyI=\n')
    ])
def test_custom_filters(template, expected_results):
    assert render(template, TEST_DATA) == expected_results

def test_render():
    assert render("template {{value}}", {"value":"123"}) == u'template 123'

    assert render({"template": "{{value}}"}, {"value":"123"}) == u'{"template": "123"}'

    assert render('{"template": {{value|json}} }', {"value":'1"23'}) == u'{"template": "1\\"23" }'

    assert render('{"template": "{{value|js}}" }', {"value":'1"23'}) == u'{"template": "1\\"23" }'

    assert render('{"template": {{value|ldap}} }', {"value":'1*23'}) == u'{"template": 1\\2a23 }'

    assert render('shell "{{value|ps}}"', {"value":'$"foo"'}) == u'shell "`$`"foo`""'

    assert render('shell "{{value|sh}}"', {"value":'$"foo"'}) == u'shell "\\$\\"foo\\""'

    assert render('template={{value|timestamp}}', {"value":0}) == u'template=0'

    assert render('template={{value|timestamp}}', {}) == u'template=null'

    assert render('template={{value|timestamp}}', {"value":{"year":2015, "month":7, "day":15}}) == u'template=1436918400000'

    assert render('template={{value|timestamp}}', {"value":datetime.datetime(2015, 7, 15)}) == u'template=1436918400000'

    assert render('{"description": "DN={{dn}}, mail={{attributes.mail[0]}}"}', TEST_ATTRIBUTES) == \
        u'{"description": "DN=uid=einstein,dc=example,dc=com, mail=einstein@ldap.forumsys.com"}'

@pytest.mark.parametrize("template, data, expected_results", [
    (
        '{"result":"{{value}}"}',
        {"value": "the" + chr(10) + "new" + chr(10) + "thing"},
        {u'result': u'the new thing'}
    ),
    (
        '{"result":"{{value}}"}',
        {"value": "the" + chr(1) + "new" + chr(9) + "thing"},
        {u'result': u'the new thing'}
    )
])
def test_render_json(template, data, expected_results):
    assert render_json(template, data) == expected_results

@pytest.mark.parametrize("override_template, default_template, payload, return_json, expected_results", [
        (TEST_OVERRIDE_TEMPLATE, TEST_DEFAULT_TEMPLATE, TEST_ATTRIBUTES, True,
         {"entryDN": "uid=einstein,dc=example,dc=com", "createTimestamp": 1393001493000}),
        (TEST_OVERRIDE_TEMPLATE, None, TEST_ATTRIBUTES, True,
         {"entryDN": "uid=einstein,dc=example,dc=com", "createTimestamp": 1393001493000}),
        (None, TEST_DEFAULT_TEMPLATE, TEST_ATTRIBUTES, True,
         {u'creatorsName': u'cn=admin,dc=example,dc=com', u'hasSubordinates': False}),
        ("bad_path.jinja", TEST_DEFAULT_TEMPLATE, TEST_ATTRIBUTES, True,
         {u'creatorsName': u'cn=admin,dc=example,dc=com', u'hasSubordinates': False}),
        (None, TEST_DEFAULT_TEMPLATE, TEST_ATTRIBUTES, False,
         '{     "creatorsName": "cn=admin,dc=example,dc=com",     "hasSubordinates": false }')
])
def test_make_payload_from_template(override_template, default_template, payload, return_json, expected_results):
    assert make_payload_from_template(override_template,
                                      default_template,
                                      payload,
                                      return_json=return_json) == expected_results

@pytest.mark.parametrize("str_date, date_format, split_at, expected_results", [
    ("2022-21-02T07:36:17", "%Y-%d-%mT%H:%M:%S", None, 1645428977000),
    ("2022-21-02T07:36:17.124Z", "%Y-%d-%mT%H:%M:%S", ".", 1645428977000),
    ("2022-02-21T07:36:17.124Z", None, ".", 1645428977000),
    ("2022-02-21T07:36:17", None, None, 1645428977000)
])
def test_soar_datetimeformat(str_date, date_format, split_at, expected_results):
    if date_format:
        assert soar_datetimeformat(str_date, date_format=date_format, split_at=split_at) == expected_results
    else:
        assert soar_datetimeformat(str_date, split_at=split_at) == expected_results


@pytest.mark.parametrize("str_value, lookup, expected_results", [
    ("low", '{ "low": "_low", "medium": "_medium", "high": "_high", "DEFAULT": "_nf" }', "_low"),
    ("nf", '{ "low": "_low", "medium": "_medium", "high": "_high", "DEFAULT": "_nf" }', "_nf"),
    ("no default", '{ "low": "_low", "medium": "_medium", "high": "_high" }', "no default")
])
def test_soar_substitute(str_value, lookup, expected_results):
    assert soar_substitute(str_value, lookup) == expected_results

@pytest.mark.parametrize("str_value, index, split_chars, expected_results", [
    ("something - here", 0, None, "something"),
    ("something - here", 1, None, "here"),
    ("something - here", 1, None, "here")
])
def test_soar_splitpart(str_value, index, split_chars, expected_results):
    if split_chars:
        assert soar_splitpart(str_value, index, split_chars=split_chars) == expected_results
    else:
        assert soar_splitpart(str_value, index) == expected_results

@pytest.mark.parametrize("str_list, expected_results", [
    ("item1", ['item1']),
    ("item1,item2", ['item1', 'item2']),
    ("item1, item2", ['item1', 'item2']),
    (" item1, item2 ", ['item1', 'item2']),
    ("", ['']),
    (None, None)
])
def test_soar_trimlist(str_list, expected_results):
    if not isinstance(str_list, type(None)):
        assert soar_trimlist(str_list.split(",")) == expected_results
    else:
        assert soar_trimlist(str_list) == expected_results


def test_global_jinja_env():
    env = global_jinja_env()

    assert isinstance(env, jinja2.environment.Environment)
    assert env.filters.get("soar_trimlist")
