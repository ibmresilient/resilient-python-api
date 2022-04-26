# -*- coding: utf-8 -*-
# pragma pylint: disable=unused-argument, no-self-use
# (c) Copyright IBM Corp. 2010, 2022. All Rights Reserved.

"""
Common methods and filters used to process 
`Jinja Templates <https://jinja.palletsprojects.com/en/3.1.x/>`_ 

**Usage:**

1. Create a Jinja template in the ``/util/templates`` directory of the App.

.. note::

    Normally a template is in JSON format:

    .. code-block::

        {
            "name": "{{ alert_name }}",
            "severity": "{{ alert_severity }}"
        }

2. (*Optional*) Add an option to your ``app.config`` file to specify an absolute
path to a custom Jinja template called: ``custom_template_path`` - if not provided the
value of ``DEFAULT_TEMPLATE_PATH`` is used.

3. Add the following code to your **Function**:

.. code-block:: python

    import pkg_resources
    from resilient_circuits import AppFunctionComponent, FunctionResult, app_function
    from resilient_lib import make_payload_from_template

    PACKAGE_NAME = "my_app"
    FN_NAME = "my_function_using_jinja"

    # Creating an absolute path to the template
    DEFAULT_TEMPLATE_PATH = pkg_resources.resource_filename(PACKAGE_NAME, "util/templates/<default_name>.jinja2")

    class FunctionComponent(AppFunctionComponent):

        def __init__(self, opts):
            super(FunctionComponent, self).__init__(opts, PACKAGE_NAME)

        @app_function(FN_NAME)
        def _app_function(self, fn_inputs):
            '''
            Function: A function showing how to use Jinja templates
            Inputs:
                -   fn_inputs.alert_severity
                -   fn_inputs.device_id
            '''

            custom_template_path = self.app_configs.custom_template_path if hasattr(self.app_configs, "custom_template_path") else ""

            template_rendered = make_payload_from_template(
                template_override=custom_template_path,
                default_template=DEFAULT_TEMPLATE_PATH,
                payload={
                    "alert_name": f"Malware found on device {fn_inputs.device_id}",
                    "alert_severity": fn_inputs.alert_severity
                },
                return_json=True
            )

            self.LOG.info(template_rendered)

            results = {"template_rendered": template_rendered}

            yield FunctionResult(results)

Output:

.. code-block:: python

    INFO [my_function_using_jinja] {'name': 'Malware found on device 303', 'severity': 'High'}

4. Update your ``README.md`` documentation file to include relevant information about the templates,
for example:

.. code-block::

    ## Templates for SOAR Cases
    It may necessary to modify the templates used to create SOAR cases based on a customer's required custom fields.
    Below are the default templates used which can be copied, modified and used with app.config's
    `custom_template_path` setting to override the default template.

    ### custom_template.jinja
    ```
    {
        "name": "{{ alert_name }}",
        "severity": "{{ alert_severity }}"
    }
    ```

======

"""

import calendar
import datetime
import json
import logging
import os
import pprint
import random
import re
import sys
import time

import pytz
from jinja2 import Environment, Undefined, select_autoescape
from jinja2.exceptions import TemplateError, TemplateSyntaxError
from resilient_lib import readable_datetime

if sys.version_info.major < 3:
    from cgi import escape as html_escape
else:
    # Python 3.2 adds html.escape() and deprecates cgi.escape().
    from html import escape as html_escape

if sys.version_info.major < 3:
    from base64 import encodestring as b64encode
else:
    # Python 3.x
    from base64 import encodebytes as b64encode

if sys.version_info.major < 3:
    from urllib import quote
else:
    # Python 3.x
    from urllib.parse import quote

LOG = logging.getLogger(__name__)

UNDEFINED_LABEL = "[undefined]"


def render(template, data):
    """
    Render data into a template, producing a string result. All the additional custom filters are available.

    :param template: Path to or a dict of the Jinja template
    :type template: str or dict
    :param data: JSON data to apply to the template
    :type data: dict
    :return: result from the rendering of the template. The template is usually a string, but can be a dict
    :rtype: str or dict

    **Examples:**

    .. code-block:: python

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
    """

    stringtemplate = template
    if isinstance(template, dict):
        stringtemplate = json.dumps(template, sort_keys=True)

    try:
        jtemplate = environment().from_string(stringtemplate)
    except TemplateSyntaxError as err:
        LOG.error("Render failed: %s, with template: %s", str(err), stringtemplate)
        raise

    try:
        stringvalue = jtemplate.render(data)
    except TemplateError:
        LOG.error("Render failed, with data: %s", data)
        raise
    return stringvalue


def render_json(template, data):
    """
    Render data into a template, producing a JSON result.
    Also clean up any "really bad" control characters to avoid failure.

    :param template: Path to or a dict of the Jinja template
    :type template: str or dict
    :param data: dict to apply to the template
    :type data: dict
    :return: result from the rendering of the template as a dictionary
    :rtype: dict

    **Examples:**

    .. code-block:: python

       >>> d = {"value": "the" + chr(10) + "new" + chr(10) + "thing"}
       >>> render_json('{"result":"{{value}}"}', d)
       {u'result': u'the new thing'}

       >>> d = {"value": "the" + chr(1) + "new" + chr(9) + "thing"}
       >>> render_json('{"result":"{{value}}"}', d)
       {u'result': u'the new thing'}
    """
    result = render(template, data)
    result = _remove_ctl_chars(result)
    return _convert_to_json(result)


def _remove_ctl_chars(result):
    # replace any control characters with spaces
    for n in range(1, 32):
        result = result.replace(chr(n), " ")
    return result


def _convert_to_json(result):
    try:
        return json.loads(result)
    except:
        raise ValueError(u"It is expected that the rendered template is a JSON Object\nInvalid JSON result: {0}".format(result))


def make_payload_from_template(template_override, default_template, payload, return_json=True):
    """
    Convert a payload into a new format based on a specified template.

    :param template_override: Path to the specified template (*usually
        taken from the app.config file. See the Usage example above*)
    :type template_override: str
    :param default_template: Path to the default template (*usually in
        the '/util/templates' directory. See the Usage example above*)
    :type default_template: str
    :param payload: ``dict`` of payload that is passed to Jinja template
    :type payload: dict
    :param return_json: False if template should be render as a ``str``
        and results returned as a ``str``
    :type return_json: bool
    :return: If the Jinja template is valid JSON and ``return_json`` is ``True`` the result is
        returned as a ``dict`` else it returns the rendered template as a ``str``
    :rtype: str|dict
    :raises ValueError: if ``return_json`` is ``True`` and the Jinja template is not
        valid JSON
    """
    template_data = _get_template(template_override, default_template)

    # Render the template.
    if return_json:
        rendered_payload = render_json(template_data, payload)
    else:
        rendered_payload = render(template_data, payload)
        rendered_payload = _remove_ctl_chars(rendered_payload)
    LOG.debug(rendered_payload)

    return rendered_payload

def _get_template(specified_template, default_template):
    """return the contents of a jinja template, either from the default location or from a customer specified
        custom path

    Args:
        specified_template ([str]): [customer specified template path]
        default_template ([str]): [default template path]

    Returns:
        [str]: [contents of template]
    """
    template_file_path = specified_template
    if template_file_path:
        if not (os.path.exists(template_file_path) and os.path.isfile(template_file_path)):
            LOG.error(u"Template file: %s doesn't exist, using default template",
                        template_file_path)
            template_file_path = None

    if not template_file_path:
        # using default template
        template_file_path = os.path.join(
                                os.path.dirname(os.path.realpath(__file__)),
                                default_template
                            )

    LOG.debug(u"template file used: %s", template_file_path)
    with open(template_file_path, "r") as definition:
        return definition.read()

# C U S T O M   J I N J A   F I L T E R S


def soar_datetimeformat(value, date_format="%Y-%m-%dT%H:%M:%S", split_at=None):
    """
    **soar_datetimeformat**

    Convert UTC dates to epoch format.

    :param value: The UTC date string
    :type value: str
    :param date_format: *(optional)* Conversion format. Defaults to ``"%Y-%m-%dT%H:%M:%S"``
    :type date_format: str
    :param split_at: *(optional)* Character to split the date field to scope the date field

        .. code-block::

            split_at='.' to remove milliseconds for "2021-10-22T20:53:53.913Z"
            split_at='+' to remove tz information "2021-10-22T20:53:53+00:00"

    :type split_at: str

    :return: Epoch value of datetime, in milliseconds
    :rtype: int
    """
    if not value:
        return value

    if split_at:
        utc_time = time.strptime(value[:value.rfind(split_at)], date_format)
    else:
        utc_time = time.strptime(value, date_format)
    return calendar.timegm(utc_time) * 1000


def soar_substitute(value, json_str):
    """
    **soar_substitute**

    Replace values based on a lookup dictionary.

    :param value: original value to lookup
    :type value: str
    :param json_str: JSON encoded string with key/value pairs of lookup values
    :type json_str: JSON encoded str
    :return: replacement value or original value if no replacement found
    :rtype: str | int
    """
    replace_dict = json.loads(json_str)
    if value in replace_dict:
        return replace_dict[value]

    # use a default value if specific match is missing
    if 'DEFAULT' in replace_dict:
        return replace_dict['DEFAULT']

    return value


def soar_splitpart(value, index, split_chars=' - '):
    """
    **soar_splitpart**

    Split a string and return the index.

    :param value: string to split
    :type value: str
    :param index: index of split to return
    :type index: int
    :param split_chars: *(optional)* split characters.  Defaults to ``' - '``
    :type split_chars: str
    :return: value of split. If ``index`` is out of bounds, the original ``value`` is returned
    :rtype: str
    """
    splits = value.split(split_chars)
    if len(splits) > index:
        return splits[index]

    return value


def soar_trimlist(org_list):
    """
    **soar_trimlist**

    Trim whitespace from elements in a list.

    :param org_list: list of elements to trim whitespace from
    :type org_list: list of strings
    :return: list with elements trimmed of whitespace
    :rtype: list
    """
    if not isinstance(org_list, list):
        return org_list
    return [element.strip() for element in org_list]


def js_filter(val):
    """
    **js**

    Produces JSONified string of the value,
    without surrounding quotes.

    :param val: The string to convert
    :type val: str
    :return: JSONified string of the value, without surrounding quotes
    :rtype: str
    """
    if val is None or isinstance(val, Undefined):
        return "null"
    js = json_filter(val)
    return js[1:-1]


def json_filter(val, indent=0):
    """
    **json**

    Produces JSONified string of the value.

    :param val: The string to convert
    :type val: str
    :return: JSONified string of the value
    :rtype: str
    """
    if val is None or isinstance(val, Undefined):
        return "null"
    return json.dumps(val, indent=indent, sort_keys=True)


def html_filter(val):
    """
    **html**

    Produces HTML-encoded string of the value.

    :param val: The string to encode
    :type val: str
    :return: Encoded string
    :rtype: str
    """
    if isinstance(val, Undefined):
        return UNDEFINED_LABEL
    return html_escape(val)


def url_filter(val):
    """
    **url**

    Produces URL-encoded string of the value.

    :param val: The string to encoded
    :type val: str
    :return: Encoded string
    :rtype: str
    """
    if isinstance(val, Undefined):
        return UNDEFINED_LABEL
    return quote(str(val))


def idna_filter(val):
    """
    **idna**

    Encodes the value per RFC 3490.

    :param val: The string to encode
    :type val: str
    :return: Encoded string
    :rtype: str
    """
    if isinstance(val, Undefined):
        return UNDEFINED_LABEL
    return val.encode("idna").decode("utf-8")


def punycode_filter(val):
    """
    **punycode**

    Encodes the value per RFC 3492.

    :param val: The string to encode
    :type val: str
    :return: Encoded string
    :rtype: str
    """
    if isinstance(val, Undefined):
        return UNDEFINED_LABEL
    return val.encode("punycode").decode("utf-8")


def ldap_filter(val):
    """
    **ldap**

    Produces LDAP-encoded string of the value.

    :param val: The string to encode
    :type val: str
    :return: Encoded string
    :rtype: str
    """
    if isinstance(val, Undefined):
        return UNDEFINED_LABEL
    escaped = []
    for char in str(val):
        if char < '0' or char > 'z' or char in "\\*()":
            char = "\\%02x" % ord(char)
        escaped.append(char)
    return ''.join(escaped)


def ps_filter(val):
    """
    **ps**

    Escapes characters in ``val`` for use in a PowerShell command line.

    :param val: The string to escaped
    :type val: str
    :return: Escaped string
    :rtype: str
    """
    if isinstance(val, Undefined):
        return UNDEFINED_LABEL
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
    """
    **sh**

    Escapes characters in ``val`` for use in a Unix shell command line.

    :param val: The string to escaped
    :type val: str
    :return: Escaped string
    :rtype: str
    """
    if isinstance(val, Undefined):
        return UNDEFINED_LABEL
    escaped = []
    for char in str(val):
        if char in "$#\"":
            char = "\\" + char
        elif ord(char) < 32 or ord(char) > 126:
            char = "\\%03o" % ord(char)
        escaped.append(char)
    return ''.join(escaped)


def pretty_filter(val, indent=2):
    """
    **pretty**

    Produces pretty-printed string of the value.

    :param val: The string to format
    :type val: str
    :param indent: Number of tabs to use when formatting
    :type indent: int
    :return: The formatted string
    :rtype: str
    """
    if isinstance(val, Undefined):
        return UNDEFINED_LABEL

    def nice_repr(obj, context, maxlevels, level):
        if sys.version_info.major < 3:
            typ = type(obj)
            if typ is unicode:
                obj = obj.encode("utf-8")
        return pprint._safe_repr(obj, context, maxlevels, level)

    printer = pprint.PrettyPrinter(indent=indent)
    printer.format = nice_repr
    return printer.pformat(val)


def iso8601(val):
    """
    **iso8601**

    Assuming ``val`` is an epoch milliseconds timestamp, produce ISO8601 datetime.

    :param val: An epoch milliseconds timestamp
    :type val: str|int
    :return: ISO8601 datetime
    :rtype: str
    """
    dt = datetime.datetime.utcfromtimestamp(int(int(val)/1000))
    return pytz.UTC.localize(dt).isoformat()


def timestamp(val):
    """
    **timestamp**

    Try convert non-timestamp values to a timestamp.

    :param val: Either ``"now"`` or a dict containing year / month / day etc.
    :type val: str | dict
    :return: An epoch milliseconds timestamp
    :rtype: int

    .. code-block::

        >>> timestamp({"year": 2018, "month": 8, "day": 1, "timezoneID": "CET"})
        1533078000000

        >>> timestamp(Undefined())
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
    if isinstance(val, Undefined):
        return "null"
    if isinstance(val, datetime.datetime):
        return int(calendar.timegm(val.utctimetuple()) * 1000)
    if val == "now":
        return int(calendar.timegm(datetime.datetime.now().utctimetuple()) * 1000)
    return val


def uniq(val, key=None):
    """
    **uniq**

    Produce the unique list.  If ``val`` is a dict, produce unique list of key values.

    :param val: The original list
    :type val: [str | int | obj]
    :param key: If ``val`` is a dict return a list with dicts with just that ``key``
    :type key: str
    :return: Original list of items with duplicates removed
    :rtype: list

    .. code-block::

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
    """
    **sample**

    Return a random sample from a list.

    :param val: List of str | obj | int
    :type val: list
    :param count: Number of times to repeat items in ``val`` to
        increase its *random* probability
    :type count: int | ``None``
    :return: The random item
    :rtype: str | obj | int
    """
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
    """
    **camel**

    Convert text to CamelCase.

    :param val: The string to convert
    :type val: str
    :return: Converted string
    :rtype: str

    .. code-block::

        This value is in camel case: {{ a#bc_def | camel }}
        >>> 'ABcDef'
    """
    titlecase = val.title()
    return re.sub(r"[\W^_]", "", titlecase)


def base64_filter(val, indent=2):
    """
    **base64**

    Breaks text into fixed-width blocks. You can specify the
    ``indent``.

    :param val: The string to convert
    :type val: str
    :param indent: Number of tabs
    :type indent: int
    :return: Converted string
    :rtype: str
    """
    if isinstance(val, Undefined):
        return ""
    s = json.dumps(val).encode("utf-8")
    return b64encode(s).decode("utf-8")


JINJA_FILTERS = {
    "json": json_filter,
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
    "base64": base64_filter,
    "soar_datetimeformat": soar_datetimeformat,
    "soar_display_datetimeformat": readable_datetime,
    "soar_substitute": soar_substitute,
    "soar_splitpart": soar_splitpart,
    "soar_trimlist": soar_trimlist
}

# Maintain one global Environment
_ENV = Environment(autoescape=select_autoescape(default_for_string=False))
_ENV.globals.update(JINJA_FILTERS)
_ENV.filters.update(JINJA_FILTERS)


def global_jinja_env():
    """
    Return the Jinja environment with our resilient-lib custom filters.
    This environment can be expanded upon to add additional custom filters.

    See `Jinja Custom Filters <https://jinja.palletsprojects.com/en/3.1.x/api/#custom-filters>`_ for more.

    Current custom filters available:

    .. parsed-literal::

        |lib_jinja_filters|


    :return: The Jinja environment
    :rtype: `jinja2.Environment <https://jinja.palletsprojects.com/en/3.1.x/api/#jinja2.Environment>`_

    **Example:**

    .. code-block:: python

        from resilient-lib import global_jinja_env

        addl_custom_filters = {
            "filter_name": method_name
        }
        env = global_jinja_env()
        env.globals.update(addl_custom_filters)
        env.filters.update(addl_custom_filters)
    """
    return _ENV


environment = global_jinja_env
