# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

TOOL_NAME = "IBM OpenAPI Spec Builder"

DEFAULT_DOC_VERSION = "1.0.0"

CHOICE_BASICAUTH = "Basic Authentication"
CHOICE_BEARER = "Bearer Token"
CHOICE_API_TOKEN = "API Token"
CHOICE_AUTH_NONE_OTHER = "None/Other"
CHOICE_LOOKUP = {
    CHOICE_BASICAUTH: "BasicAuth",
    CHOICE_BEARER: "BearerAuth",
    CHOICE_API_TOKEN: "ApiKeyAuth"
}

CHOICE_YES = "Yes"
CHOICE_NO = "No"
CHOICE_EXIT = "Exit"

NONE_TYPE = "None"
OBJECT_TYPE = "object"

VALUE_STRING = "string"
VALUE_INTEGER = "integer"
VALUE_NUMBER = "number"
VALUE_BOOLEAN = "boolean"
VALUE_ARRAY = "array"
VALUE_TYPES = [VALUE_STRING, VALUE_INTEGER, VALUE_NUMBER, VALUE_BOOLEAN, VALUE_ARRAY, OBJECT_TYPE]
API_CALL_METHOD_GET = "GET"
API_CALL_METHODS = [API_CALL_METHOD_GET, "PUT", "POST", "DELETE", "PATCH"]
VALID_API_CALL_METHODS = ["get", "put", "post", "delete", "patch", "head", "trace"]
API_PARAMETER_TYPE = ["query", "path"]
API_PARAMETER_REQUIRED = [True, False]

DEFAULT_OPENAPI_VERSION = "3.0.0"
VALIDATE_OPENAPI_VERSION= "3.1.0"

CONTENT_TYPE_APPLICATION_JSON = "application/json"
CONTENT_TYPE_APPLICATION_XML = "application/xml"
CONTENT_TYPE_URLENCODED = "application/x-www-form-urlencoded"
CONTENT_TYPE_TEXT = "text/plain"
CONTENT_TYPE_UNDEFINED = "undefined"
CONTENT_TYPE_SPECIFY = "input new type"

# "multipart/form-data"
CONTENT_TYPES = [CONTENT_TYPE_APPLICATION_JSON,
                 CONTENT_TYPE_APPLICATION_XML,
                 CONTENT_TYPE_URLENCODED,
                 CONTENT_TYPE_TEXT,
                 CONTENT_TYPE_UNDEFINED,
                 CONTENT_TYPE_SPECIFY]

RESPONSE_FORMAT_JSON = "json"
RESPONSE_FORMAT_XML = "xml"
RESPONSE_FORMAT_SCHEMA = "schema"

RESPONSE_FORMATS = [RESPONSE_FORMAT_JSON, RESPONSE_FORMAT_SCHEMA, NONE_TYPE]

PATH_PARAMS_REXEG = r"\{(\w*)\}"

END_WITH_EMPTY_LINE = "(Return/Enter skips input)"
ERROR_MARKER = "***"

SECURITY_TYPES = {
    CHOICE_BASICAUTH: (CHOICE_LOOKUP[CHOICE_BASICAUTH],
                       {
                            "type": "http",
                            "scheme": "basic"
                       }),
    CHOICE_BEARER: (CHOICE_LOOKUP[CHOICE_BEARER],
                    {
                        "type": "http",
                        "scheme": "bearer"
                    }),
    CHOICE_API_TOKEN: (CHOICE_LOOKUP[CHOICE_API_TOKEN],
                        {
                            "type": "apiKey",
                            "in": "header",
                            "name": "X-API-Key"
                        })
}

API_KEY_QUERY = "query"
API_KEY_HEADER = "header"

# file used to validate openapi files for correct format
DATA_FOLDER = "data"
OPENAPI_SPEC_3_0 = "openapi_spec_3.1.json"

INTERNAL_REF = "$ref"

SPEC_OPENAPI = "openapi"
SPEC_OPENAPI_PATH = [SPEC_OPENAPI]
SPEC_INFO_PATH = ["info"]
SPEC_EXTERNAL_DOCS_PATH = ["externalDocs"]
SPEC_SERVERS_PATH = ["servers"]
SPEC_PATHS_PATH = ["paths"]
SPEC_PARAMETERS_PATH = ["components", "parameters"]
SPEC_HEADERS_PATH = ["components", "headers"]
SPEC_SECURITY_SCHEMES_PATH = ["components", "securitySchemes"]
SPEC_SCHEMAS_PATH = ["components", "schemas"]
SPEC_TAGS_PATH = ["tags"]

# $ref or in-line style parameters
IN_LINE_REFERENCES = True
