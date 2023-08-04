{
    "action_order": [],
    "actions": [
      {
        "automations": [],
        "conditions": [
          {
            "evaluation_id": 3,
            "field_name": "incident.pii.alberta_health_risk_assessment",
            "method": "changed_to",
            "type": null,
            "value": false
          },
          {
            "evaluation_id": 2,
            "field_name": "milestone.date",
            "method": "due_within",
            "type": null,
            "value": 5
          },
          {
            "evaluation_id": 1,
            "field_name": null,
            "method": "object_added",
            "type": null,
            "value": null
          }
        ],
        "custom_condition": "3 AND (2 OR 1) AND 2",
        "enabled": true,
        "export_key": "test_rule_conditions",
        "id": 205,
        "logic_type": "advanced",
        "message_destinations": [],
        "name": "test_rule_conditions",
        "object_type": "milestone",
        "tags": [],
        "timeout_seconds": 86400,
        "type": 0,
        "uuid": "272f95fb-e609-4c53-a82f-b2420c5e1076",
        "view_items": [],
        "workflows": []
      },
      {
        "automations": [],
        "conditions": [
          {
            "evaluation_id": 1,
            "field_name": "incident.city",
            "method": "not_has_a_value",
            "type": null,
            "value": null
          },
          {
            "evaluation_id": 2,
            "field_name": "incident.severity_code",
            "method": "equals",
            "type": null,
            "value": "Medium"
          }
        ],
        "custom_condition": "1 AND 2 OR 1",
        "enabled": true,
        "export_key": "test_rule_conditions_manual",
        "id": 209,
        "logic_type": "advanced",
        "message_destinations": [],
        "name": "test_rule_conditions_manual",
        "object_type": "incident",
        "tags": [],
        "timeout_seconds": 86400,
        "type": 1,
        "uuid": "129523ae-7c43-4745-953d-063d431e5c05",
        "view_items": [],
        "workflows": []
      }
    ],
    "apps": [],
    "automatic_tasks": [],
    "case_matching_profiles": [],
    "export_date": 1691158480252,
    "export_format_version": 2,
    "export_type": null,
    "fields": [
      {
        "allow_default_value": false,
        "blank_option": false,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/fn_test_dynamic_input_str_intput2",
        "hide_notification": false,
        "id": 3286,
        "input_type": "text",
        "internal": false,
        "is_tracked": false,
        "name": "fn_test_dynamic_input_str_intput2",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [],
        "text": "fn_test_dynamic_input_str_intput2",
        "tooltip": "",
        "type_id": 11,
        "uuid": "82558e82-1d2e-4cc8-ab15-0650e34cf984",
        "values": []
      },
      {
        "allow_default_value": false,
        "blank_option": false,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/fn_test_dynamic_input_str_intput4",
        "hide_notification": false,
        "id": 3288,
        "input_type": "text",
        "internal": false,
        "is_tracked": false,
        "name": "fn_test_dynamic_input_str_intput4",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [],
        "text": "fn_test_dynamic_input_str_intput4",
        "tooltip": "",
        "type_id": 11,
        "uuid": "c4f4a4ed-bd5c-46be-8d05-9569398d2497",
        "values": []
      },
      {
        "allow_default_value": false,
        "blank_option": false,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/text_with_string_1",
        "hide_notification": false,
        "id": 3291,
        "input_type": "textarea",
        "internal": false,
        "is_tracked": false,
        "name": "text_with_string_1",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [
          {
            "id": 7,
            "name": "Entry 2",
            "template": {
              "content": "entry_2",
              "format": "text"
            },
            "uuid": "591ae780-5e06-4708-a968-45bbb848dd32"
          },
          {
            "id": 8,
            "name": "Entry 1",
            "template": {
              "content": "entry_1",
              "format": "text"
            },
            "uuid": "ab17581c-c48f-47f4-8783-266a3f2390ad"
          }
        ],
        "text": "text_with_string_1",
        "tooltip": "",
        "type_id": 11,
        "uuid": "d6f0aa8e-bf2e-43b2-88f7-c4cc57d8c73b",
        "values": []
      },
      {
        "allow_default_value": false,
        "blank_option": false,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/fn_test_dynamic_input_str_intput5",
        "hide_notification": false,
        "id": 3289,
        "input_type": "text",
        "internal": false,
        "is_tracked": false,
        "name": "fn_test_dynamic_input_str_intput5",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [],
        "text": "fn_test_dynamic_input_str_intput5",
        "tooltip": "",
        "type_id": 11,
        "uuid": "f17081c8-ee6c-4a31-9c5a-1de955bbdec6",
        "values": []
      },
      {
        "allow_default_value": false,
        "blank_option": false,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/fn_test_dynamic_input_str_input",
        "hide_notification": false,
        "id": 3285,
        "input_type": "text",
        "internal": false,
        "is_tracked": false,
        "name": "fn_test_dynamic_input_str_input",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [],
        "text": "fn_test_dynamic_input_str_input",
        "tooltip": "",
        "type_id": 11,
        "uuid": "f8ba640d-57f7-407b-9c5d-03273ab619fc",
        "values": []
      },
      {
        "allow_default_value": false,
        "blank_option": false,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/date_picker_1",
        "hide_notification": false,
        "id": 3294,
        "input_type": "datepicker",
        "internal": false,
        "is_tracked": false,
        "name": "date_picker_1",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [],
        "text": "date_picker_1",
        "tooltip": "",
        "type_id": 11,
        "uuid": "fa2e6b92-0926-452e-88a8-84058b2b5917",
        "values": []
      },
      {
        "allow_default_value": false,
        "blank_option": true,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/select_1",
        "hide_notification": false,
        "id": 3290,
        "input_type": "select",
        "internal": false,
        "is_tracked": false,
        "name": "select_1",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [],
        "text": "select_1",
        "tooltip": "",
        "type_id": 11,
        "uuid": "00de775f-81bc-4446-a2d1-fa98d9b03b22",
        "values": [
          {
            "default": true,
            "enabled": true,
            "hidden": false,
            "label": "A",
            "properties": null,
            "uuid": "9c8df467-e4b8-481e-9f8d-ce41b3af8049",
            "value": 2552
          },
          {
            "default": false,
            "enabled": true,
            "hidden": false,
            "label": "B",
            "properties": null,
            "uuid": "5c9df2ec-9bbd-4ff5-9fda-8b5b1c5da772",
            "value": 2553
          },
          {
            "default": false,
            "enabled": true,
            "hidden": false,
            "label": "C",
            "properties": null,
            "uuid": "2085f811-2f1d-47c5-a867-6360ad0108dc",
            "value": 2554
          },
          {
            "default": false,
            "enabled": true,
            "hidden": false,
            "label": "D",
            "properties": null,
            "uuid": "1c738ea4-a502-4c18-ac13-2eaedbaaa6b4",
            "value": 2555
          }
        ]
      },
      {
        "allow_default_value": false,
        "blank_option": false,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/multiselect_1",
        "hide_notification": false,
        "id": 3292,
        "input_type": "multiselect",
        "internal": false,
        "is_tracked": false,
        "name": "multiselect_1",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [],
        "text": "multiselect_1",
        "tooltip": "",
        "type_id": 11,
        "uuid": "3be01039-6e1b-4efb-8689-7886d519f79a",
        "values": [
          {
            "default": false,
            "enabled": true,
            "hidden": false,
            "label": "W",
            "properties": null,
            "uuid": "f0861fb7-b9e9-446f-a45d-ce49d1c5541c",
            "value": 2556
          },
          {
            "default": false,
            "enabled": true,
            "hidden": false,
            "label": "X",
            "properties": null,
            "uuid": "252a0972-f966-4faa-b9dc-d1f2b69a3f6c",
            "value": 2557
          },
          {
            "default": false,
            "enabled": true,
            "hidden": false,
            "label": "Y",
            "properties": null,
            "uuid": "4ff54f2c-fcee-4149-927a-ddb6222cb9a7",
            "value": 2558
          },
          {
            "default": false,
            "enabled": true,
            "hidden": false,
            "label": "Z",
            "properties": null,
            "uuid": "579d065e-e988-459f-8347-b9c40ff57a3b",
            "value": 2559
          }
        ]
      },
      {
        "allow_default_value": false,
        "blank_option": false,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/boolean_1",
        "hide_notification": false,
        "id": 3293,
        "input_type": "boolean",
        "internal": false,
        "is_tracked": false,
        "name": "boolean_1",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [],
        "text": "boolean_1",
        "tooltip": "",
        "type_id": 11,
        "uuid": "56cf80ab-3255-43d1-805e-17f003ff83a9",
        "values": []
      },
      {
        "allow_default_value": false,
        "blank_option": false,
        "calculated": false,
        "changeable": true,
        "chosen": false,
        "default_chosen_by_server": false,
        "deprecated": false,
        "export_key": "__function/fn_test_dynamic_input_str_intput3",
        "hide_notification": false,
        "id": 3287,
        "input_type": "text",
        "internal": false,
        "is_tracked": false,
        "name": "fn_test_dynamic_input_str_intput3",
        "operation_perms": {},
        "operations": [],
        "placeholder": "",
        "prefix": null,
        "read_only": false,
        "rich_text": false,
        "tags": [],
        "templates": [],
        "text": "fn_test_dynamic_input_str_intput3",
        "tooltip": "",
        "type_id": 11,
        "uuid": "726a7b83-495a-4365-9432-9deddfa7ae04",
        "values": []
      },
      {
        "export_key": "incident/internal_customizations_field",
        "id": 0,
        "input_type": "text",
        "internal": true,
        "name": "internal_customizations_field",
        "read_only": true,
        "text": "Customizations Field (internal)",
        "type_id": 0,
        "uuid": "bfeec2d4-3770-11e8-ad39-4a0004044aa1"
      }
    ],
    "functions": [
      {
        "created_date": 1690813429793,
        "description": {
          "content": null,
          "format": "text"
        },
        "destination_handle": "fn_test_dynamic_input",
        "display_name": "fn_test_dynamic_input",
        "export_key": "fn_test_dynamic_input",
        "id": 90,
        "last_modified_by": {
          "display_name": "Admin User",
          "id": 1,
          "name": "admin@example.com",
          "type": "user"
        },
        "last_modified_time": 1690898203196,
        "name": "fn_test_dynamic_input",
        "output_description": {
          "content": null,
          "format": "text"
        },
        "tags": [],
        "uuid": "faddd76e-7e40-4fd4-bed9-511410b2acfe",
        "version": 4,
        "view_items": [
          {
            "content": "f8ba640d-57f7-407b-9c5d-03273ab619fc",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          },
          {
            "content": "82558e82-1d2e-4cc8-ab15-0650e34cf984",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          },
          {
            "content": "726a7b83-495a-4365-9432-9deddfa7ae04",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          },
          {
            "content": "c4f4a4ed-bd5c-46be-8d05-9569398d2497",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          },
          {
            "content": "f17081c8-ee6c-4a31-9c5a-1de955bbdec6",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          },
          {
            "content": "00de775f-81bc-4446-a2d1-fa98d9b03b22",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          },
          {
            "content": "d6f0aa8e-bf2e-43b2-88f7-c4cc57d8c73b",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          },
          {
            "content": "3be01039-6e1b-4efb-8689-7886d519f79a",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          },
          {
            "content": "56cf80ab-3255-43d1-805e-17f003ff83a9",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          },
          {
            "content": "fa2e6b92-0926-452e-88a8-84058b2b5917",
            "element": "field_uuid",
            "field_type": "__function",
            "show_if": null,
            "show_link_header": false,
            "step_label": null
          }
        ],
        "workflows": []
      }
    ],
    "geos": null,
    "groups": null,
    "id": 69,
    "inbound_destinations": [],
    "inbound_mailboxes": null,
    "incident_artifact_types": [],
    "incident_types": [
      {
        "create_date": 1691158477148,
        "description": "Customization Packages (internal)",
        "enabled": false,
        "export_key": "Customization Packages (internal)",
        "hidden": false,
        "id": 0,
        "name": "Customization Packages (internal)",
        "parent_id": null,
        "system": false,
        "update_date": 1691158477148,
        "uuid": "bfeec2d4-3770-11e8-ad39-4a0004044aa0"
      }
    ],
    "layouts": [],
    "locale": null,
    "message_destinations": [
      {
        "api_keys": [
          "ad261c1f-f1cc-4115-bbce-a151f88bac5e"
        ],
        "destination_type": 0,
        "expect_ack": true,
        "export_key": "fn_test_dynamic_input",
        "name": "fn_test_dynamic_input",
        "programmatic_name": "fn_test_dynamic_input",
        "tags": [],
        "users": [],
        "uuid": "fcab029f-0a0a-471a-aa48-4495b3ac6d82"
      }
    ],
    "notifications": null,
    "overrides": null,
    "phases": [],
    "playbooks": [
      {
        "activation_type": "manual",
        "content": {
          "content_version": 48,
          "xml": "\u003c?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?\u003e\u003cdefinitions xmlns=\"http://www.omg.org/spec/BPMN/20100524/MODEL\" xmlns:bpmndi=\"http://www.omg.org/spec/BPMN/20100524/DI\" xmlns:omgdc=\"http://www.omg.org/spec/DD/20100524/DC\" xmlns:omgdi=\"http://www.omg.org/spec/DD/20100524/DI\" xmlns:resilient=\"http://resilient.ibm.com/bpmn\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" targetNamespace=\"http://www.camunda.org/test\"\u003e\u003cprocess id=\"playbook_8b2bacb8_9423_4de7_b9d1_4f6dc701e2e8\" isExecutable=\"true\" name=\"playbook_8b2bacb8_9423_4de7_b9d1_4f6dc701e2e8\"\u003e\u003cdocumentation/\u003e\u003cstartEvent id=\"StartEvent_155asxm\"\u003e\u003coutgoing\u003eFlow_0xtv30k\u003c/outgoing\u003e\u003c/startEvent\u003e\u003cserviceTask id=\"ServiceTask_1\" name=\"fn_test_dynamic_input\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"faddd76e-7e40-4fd4-bed9-511410b2acfe\"\u003e{\"inputs\":{\"f8ba640d-57f7-407b-9c5d-03273ab619fc\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"This is some text, but here is ${INPUT}\"}},\"82558e82-1d2e-4cc8-ab15-0650e34cf984\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"Normal except also keyring: ^{test_keyring}. But now also env: ${INPUT}\"}},\"726a7b83-495a-4365-9432-9deddfa7ae04\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"$STANDARD_NOT_FOUND\"}},\"c4f4a4ed-bd5c-46be-8d05-9569398d2497\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"$INPUT\"}},\"f17081c8-ee6c-4a31-9c5a-1de955bbdec6\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"This is some text, but here is ${INPUT} but then also some ${NOT_FOUND}\"}},\"00de775f-81bc-4446-a2d1-fa98d9b03b22\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"select_value\":\"9c8df467-e4b8-481e-9f8d-ce41b3af8049\"}},\"d6f0aa8e-bf2e-43b2-88f7-c4cc57d8c73b\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_content_value\":{\"format\":\"unknown\",\"content\":\"entry_1\"}}},\"3be01039-6e1b-4efb-8689-7886d519f79a\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[\"252a0972-f966-4faa-b9dc-d1f2b69a3f6c\"]}},\"56cf80ab-3255-43d1-805e-17f003ff83a9\":{\"input_type\":\"static\",\"static_input\":{\"boolean_value\":false,\"multiselect_value\":[]}},\"fa2e6b92-0926-452e-88a8-84058b2b5917\":{\"input_type\":\"static\",\"static_input\":{\"date_value\":1691020800000,\"multiselect_value\":[]}}},\"result_name\":\"output\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_0xtv30k\u003c/incoming\u003e\u003coutgoing\u003eFlow_0zyhrv6\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003cendEvent id=\"EndPoint_2\" resilient:documentation=\"End point\"\u003e\u003cincoming\u003eFlow_1izq1da\u003c/incoming\u003e\u003c/endEvent\u003e\u003csequenceFlow id=\"Flow_0zyhrv6\" sourceRef=\"ServiceTask_1\" targetRef=\"ServiceTask_4\"/\u003e\u003csequenceFlow id=\"Flow_0xtv30k\" sourceRef=\"StartEvent_155asxm\" targetRef=\"ServiceTask_1\"/\u003e\u003cscriptTask id=\"ScriptTask_3\" name=\"a local script\"\u003e\u003cextensionElements\u003e\u003cresilient:script uuid=\"1dcc0534-9dbb-4872-88c9-0716f74d7de6\"/\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_0vqo5z8\u003c/incoming\u003e\u003coutgoing\u003eFlow_1izq1da\u003c/outgoing\u003e\u003cscript\u003escript\u003c/script\u003e\u003c/scriptTask\u003e\u003csequenceFlow id=\"Flow_1izq1da\" sourceRef=\"ScriptTask_3\" targetRef=\"EndPoint_2\"/\u003e\u003cserviceTask id=\"ServiceTask_4\" name=\"fn_test_dynamic_input\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"faddd76e-7e40-4fd4-bed9-511410b2acfe\"\u003e{\"inputs\":{\"f8ba640d-57f7-407b-9c5d-03273ab619fc\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"82558e82-1d2e-4cc8-ab15-0650e34cf984\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"726a7b83-495a-4365-9432-9deddfa7ae04\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"c4f4a4ed-bd5c-46be-8d05-9569398d2497\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"f17081c8-ee6c-4a31-9c5a-1de955bbdec6\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"00de775f-81bc-4446-a2d1-fa98d9b03b22\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"select_value\":\"9c8df467-e4b8-481e-9f8d-ce41b3af8049\"}},\"d6f0aa8e-bf2e-43b2-88f7-c4cc57d8c73b\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_content_value\":{\"format\":\"unknown\",\"content\":\"\"}}},\"3be01039-6e1b-4efb-8689-7886d519f79a\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"56cf80ab-3255-43d1-805e-17f003ff83a9\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"fa2e6b92-0926-452e-88a8-84058b2b5917\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}}},\"pre_processing_script\":\"\\\"\\\"\\\"pre script\\n\\\"\\\"\\\"\",\"pre_processing_script_language\":\"python3\",\"result_name\":\"output2\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_0zyhrv6\u003c/incoming\u003e\u003coutgoing\u003eFlow_0vqo5z8\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003csequenceFlow id=\"Flow_0vqo5z8\" sourceRef=\"ServiceTask_4\" targetRef=\"ScriptTask_3\"/\u003e\u003c/process\u003e\u003cbpmndi:BPMNDiagram id=\"BPMNDiagram_1\"\u003e\u003cbpmndi:BPMNPlane bpmnElement=\"playbook_8b2bacb8_9423_4de7_b9d1_4f6dc701e2e8\" id=\"BPMNPlane_1\"\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_0vqo5z8\" id=\"Flow_0vqo5z8_di\"\u003e\u003comgdi:waypoint x=\"721\" y=\"472\"/\u003e\u003comgdi:waypoint x=\"721\" y=\"558.25\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_1izq1da\" id=\"Flow_1izq1da_di\"\u003e\u003comgdi:waypoint x=\"721\" y=\"642\"/\u003e\u003comgdi:waypoint x=\"721\" y=\"714\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_0xtv30k\" id=\"Flow_0xtv30k_di\"\u003e\u003comgdi:waypoint x=\"721\" y=\"117\"/\u003e\u003comgdi:waypoint x=\"721\" y=\"218\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_0zyhrv6\" id=\"Flow_0zyhrv6_di\"\u003e\u003comgdi:waypoint x=\"721\" y=\"302\"/\u003e\u003comgdi:waypoint x=\"721\" y=\"388\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNShape bpmnElement=\"StartEvent_155asxm\" id=\"StartEvent_155asxm_di\"\u003e\u003comgdc:Bounds height=\"52\" width=\"187.083\" x=\"627\" y=\"65\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"0\" width=\"90\" x=\"616\" y=\"100\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_1\" id=\"ServiceTask_1_di\"\u003e\u003comgdc:Bounds height=\"84\" width=\"196\" x=\"623\" y=\"218\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"EndPoint_2\" id=\"EndPoint_2_di\"\u003e\u003comgdc:Bounds height=\"52\" width=\"132.15\" x=\"655\" y=\"714\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ScriptTask_3\" id=\"ScriptTask_3_di\"\u003e\u003comgdc:Bounds height=\"84\" width=\"196\" x=\"622.5\" y=\"558.25\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_4\" id=\"ServiceTask_4_di\"\u003e\u003comgdc:Bounds height=\"84\" width=\"196\" x=\"622.75\" y=\"388\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003c/bpmndi:BPMNPlane\u003e\u003c/bpmndi:BPMNDiagram\u003e\u003c/definitions\u003e"
        },
        "create_date": 1690813455360,
        "creator_principal": {
          "display_name": "Admin User",
          "id": 1,
          "name": "admin@example.com",
          "type": "user"
        },
        "deployment_id": "playbook_8b2bacb8_9423_4de7_b9d1_4f6dc701e2e8",
        "description": {
          "content": null,
          "format": "text"
        },
        "display_name": "fn_test_dynamic_input",
        "export_key": "fn_test_dynamic_input",
        "field_type_handle": "playbook_8b2bacb8_9423_4de7_b9d1_4f6dc701e2e8",
        "fields_type": {
          "actions": [],
          "display_name": "fn_test_dynamic_input",
          "export_key": "playbook_8b2bacb8_9423_4de7_b9d1_4f6dc701e2e8",
          "fields": {},
          "for_actions": false,
          "for_custom_fields": false,
          "for_notifications": false,
          "for_workflows": false,
          "id": null,
          "parent_types": [
            "__playbook"
          ],
          "properties": {
            "can_create": false,
            "can_destroy": false,
            "for_who": []
          },
          "scripts": [],
          "tags": [],
          "type_id": 28,
          "type_name": "playbook_8b2bacb8_9423_4de7_b9d1_4f6dc701e2e8",
          "uuid": "971225ad-6be6-4b1d-be88-7636708793c8"
        },
        "has_logical_errors": false,
        "id": 21,
        "is_deleted": false,
        "is_locked": false,
        "last_modified_principal": {
          "display_name": "Admin User",
          "id": 1,
          "name": "admin@example.com",
          "type": "user"
        },
        "last_modified_time": 1691158468304,
        "local_scripts": [
          {
            "actions": [],
            "created_date": 1690921225759,
            "description": "",
            "enabled": false,
            "export_key": "a local script",
            "id": 34,
            "language": "python3",
            "last_modified_by": "admin@example.com",
            "last_modified_time": 1690990151511,
            "name": "a local script",
            "object_type": "incident",
            "playbook_handle": "fn_test_dynamic_input",
            "programmatic_name": "fn_test_dynamic_input_a_local_script",
            "script_text": "a_variable = \"a string\"\nb_variable = \"b string\"\nc_variable = 12345\n# d_variable = playbook.functions.results.output\nd_variable = playbook.functions.results.output2\no = \"output\"",
            "tags": [],
            "uuid": "1dcc0534-9dbb-4872-88c9-0716f74d7de6"
          }
        ],
        "manual_settings": {
          "activation_conditions": {
            "conditions": [
              {
                "evaluation_id": null,
                "field_name": "incident.addr",
                "method": "has_a_value",
                "type": null,
                "value": null
              },
              {
                "evaluation_id": null,
                "field_name": "incident.creator_id",
                "method": "equals",
                "type": null,
                "value": "admin@example.com"
              }
            ],
            "logic_type": "all"
          },
          "view_items": []
        },
        "name": "fn_test_dynamic_input",
        "object_type": "incident",
        "status": "enabled",
        "tag": {
          "display_name": "Playbook_8b2bacb8-9423-4de7-b9d1-4f6dc701e2e8",
          "id": 31,
          "name": "playbook_8b2bacb8_9423_4de7_b9d1_4f6dc701e2e8",
          "type": "playbook",
          "uuid": "ffa7c9f6-5b2e-45a0-9cb7-afd3336497c2"
        },
        "tags": [],
        "type": "default",
        "uuid": "8b2bacb8-9423-4de7-b9d1-4f6dc701e2e8",
        "version": 53
      },
      {
        "activation_type": "manual",
        "content": {
          "content_version": 6,
          "xml": "\u003c?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?\u003e\u003cdefinitions xmlns=\"http://www.omg.org/spec/BPMN/20100524/MODEL\" xmlns:bpmndi=\"http://www.omg.org/spec/BPMN/20100524/DI\" xmlns:omgdc=\"http://www.omg.org/spec/DD/20100524/DC\" xmlns:omgdi=\"http://www.omg.org/spec/DD/20100524/DI\" xmlns:resilient=\"http://resilient.ibm.com/bpmn\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" targetNamespace=\"http://www.camunda.org/test\"\u003e\u003cprocess id=\"playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf\" isExecutable=\"true\" name=\"playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf\"\u003e\u003cdocumentation/\u003e\u003cstartEvent id=\"StartEvent_155asxm\"\u003e\u003coutgoing\u003eFlow_0lcu5o1\u003c/outgoing\u003e\u003c/startEvent\u003e\u003cserviceTask id=\"ServiceTask_1\" name=\"fn_test_dynamic_input\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"faddd76e-7e40-4fd4-bed9-511410b2acfe\"\u003e{\"inputs\":{\"f8ba640d-57f7-407b-9c5d-03273ab619fc\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"82558e82-1d2e-4cc8-ab15-0650e34cf984\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"726a7b83-495a-4365-9432-9deddfa7ae04\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"c4f4a4ed-bd5c-46be-8d05-9569398d2497\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"f17081c8-ee6c-4a31-9c5a-1de955bbdec6\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_value\":\"\"}},\"00de775f-81bc-4446-a2d1-fa98d9b03b22\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"select_value\":\"9c8df467-e4b8-481e-9f8d-ce41b3af8049\"}},\"d6f0aa8e-bf2e-43b2-88f7-c4cc57d8c73b\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_content_value\":{\"format\":\"unknown\",\"content\":\"\"}}},\"3be01039-6e1b-4efb-8689-7886d519f79a\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"56cf80ab-3255-43d1-805e-17f003ff83a9\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}},\"fa2e6b92-0926-452e-88a8-84058b2b5917\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[]}}},\"result_name\":\"output\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_0lcu5o1\u003c/incoming\u003e\u003coutgoing\u003eFlow_09fbf0c\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003cendEvent id=\"EndPoint_2\" resilient:documentation=\"End point\"\u003e\u003cextensionElements\u003e\u003cresilient:endEvent\u003e{\"script\":\"playbook.results = playbook.functions.results.output\",\"script_language\":\"python3\"}\u003c/resilient:endEvent\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_09fbf0c\u003c/incoming\u003e\u003c/endEvent\u003e\u003csequenceFlow id=\"Flow_0lcu5o1\" sourceRef=\"StartEvent_155asxm\" targetRef=\"ServiceTask_1\"/\u003e\u003csequenceFlow id=\"Flow_09fbf0c\" sourceRef=\"ServiceTask_1\" targetRef=\"EndPoint_2\"/\u003e\u003c/process\u003e\u003cbpmndi:BPMNDiagram id=\"BPMNDiagram_1\"\u003e\u003cbpmndi:BPMNPlane bpmnElement=\"playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf\" id=\"BPMNPlane_1\"\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_09fbf0c\" id=\"Flow_09fbf0c_di\"\u003e\u003comgdi:waypoint x=\"730\" y=\"392\"/\u003e\u003comgdi:waypoint x=\"730\" y=\"524\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_0lcu5o1\" id=\"Flow_0lcu5o1_di\"\u003e\u003comgdi:waypoint x=\"730\" y=\"117\"/\u003e\u003comgdi:waypoint x=\"730\" y=\"308\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNShape bpmnElement=\"StartEvent_155asxm\" id=\"StartEvent_155asxm_di\"\u003e\u003comgdc:Bounds height=\"52\" width=\"199.65\" x=\"630\" y=\"65\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"0\" width=\"90\" x=\"616\" y=\"100\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_1\" id=\"ServiceTask_1_di\"\u003e\u003comgdc:Bounds height=\"84\" width=\"196\" x=\"632\" y=\"308\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"EndPoint_2\" id=\"EndPoint_2_di\"\u003e\u003comgdc:Bounds height=\"52\" width=\"132.15\" x=\"664\" y=\"524\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003c/bpmndi:BPMNPlane\u003e\u003c/bpmndi:BPMNDiagram\u003e\u003c/definitions\u003e"
        },
        "create_date": 1691092968036,
        "creator_principal": {
          "display_name": "Admin User",
          "id": 1,
          "name": "admin@example.com",
          "type": "user"
        },
        "deployment_id": "playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf",
        "description": {
          "content": null,
          "format": "text"
        },
        "display_name": "test_sub_playbook",
        "export_key": "subplaybook_test_sub_playbook",
        "field_type_handle": "playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf",
        "fields_type": {
          "actions": [],
          "display_name": "test_sub_playbook",
          "export_key": "playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf",
          "fields": {
            "bool": {
              "allow_default_value": false,
              "blank_option": false,
              "calculated": false,
              "changeable": true,
              "chosen": false,
              "default_chosen_by_server": false,
              "deprecated": false,
              "export_key": "playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf/bool",
              "hide_notification": false,
              "id": 3295,
              "input_type": "boolean",
              "internal": false,
              "is_tracked": false,
              "name": "bool",
              "operation_perms": {},
              "operations": [],
              "placeholder": "",
              "prefix": null,
              "read_only": false,
              "rich_text": false,
              "tags": [],
              "templates": [],
              "text": "bool",
              "tooltip": "",
              "type_id": 1028,
              "uuid": "6b934067-7a03-4765-a378-3df3a146a5ce",
              "values": []
            }
          },
          "for_actions": false,
          "for_custom_fields": false,
          "for_notifications": false,
          "for_workflows": false,
          "id": null,
          "parent_types": [
            "__playbook"
          ],
          "properties": {
            "can_create": false,
            "can_destroy": false,
            "for_who": []
          },
          "scripts": [],
          "tags": [],
          "type_id": 28,
          "type_name": "playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf",
          "uuid": "5c397e98-0167-4761-924a-cc230c177635"
        },
        "has_logical_errors": false,
        "id": 24,
        "is_deleted": false,
        "is_locked": false,
        "last_modified_principal": {
          "display_name": "Admin User",
          "id": 1,
          "name": "admin@example.com",
          "type": "user"
        },
        "last_modified_time": 1691095066711,
        "local_scripts": [],
        "name": "subplaybook_test_sub_playbook",
        "object_type": "qradar_reference_set",
        "status": "enabled",
        "subplaybook_settings": {
          "common_script": false,
          "output_description": {
            "content": null,
            "format": "text"
          },
          "output_json_example": "",
          "output_json_schema": "",
          "view_items": [
            {
              "content": "6b934067-7a03-4765-a378-3df3a146a5ce",
              "element": "field_uuid",
              "field_type": "playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf",
              "show_if": null,
              "show_link_header": false,
              "step_label": null
            }
          ]
        },
        "tag": {
          "display_name": "Playbook_9e580fbd-5c66-4246-9ea4-e2379ea13ebf",
          "id": 34,
          "name": "playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf",
          "type": "playbook",
          "uuid": "47672258-7f16-47b7-92d1-5a8ec0162645"
        },
        "tags": [],
        "type": "subplaybook",
        "uuid": "9e580fbd-5c66-4246-9ea4-e2379ea13ebf",
        "version": 11
      },
      {
        "activation_details": {
          "activation_conditions": {
            "conditions": [
              {
                "evaluation_id": 2,
                "field_name": "incident.plan_status",
                "method": "has_a_value",
                "type": null,
                "value": null
              },
              {
                "evaluation_id": 4,
                "field_name": "qradar_reference_set.qradar_server",
                "method": "contains",
                "type": null,
                "value": "a third thing"
              },
              {
                "evaluation_id": 3,
                "field_name": "qradar_reference_set.reference_set",
                "method": "changed",
                "type": null,
                "value": null
              },
              {
                "evaluation_id": 1,
                "field_name": null,
                "method": "object_added",
                "type": null,
                "value": null
              }
            ],
            "custom_condition": "4 OR 3 OR 2 OR1",
            "logic_type": "advanced"
          }
        },
        "activation_type": "automatic",
        "content": {
          "content_version": 10,
          "xml": "\u003c?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?\u003e\u003cdefinitions xmlns=\"http://www.omg.org/spec/BPMN/20100524/MODEL\" xmlns:bpmndi=\"http://www.omg.org/spec/BPMN/20100524/DI\" xmlns:camunda=\"http://camunda.org/schema/1.0/bpmn\" xmlns:omgdc=\"http://www.omg.org/spec/DD/20100524/DC\" xmlns:omgdi=\"http://www.omg.org/spec/DD/20100524/DI\" xmlns:resilient=\"http://resilient.ibm.com/bpmn\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" targetNamespace=\"http://www.camunda.org/test\"\u003e\u003cprocess id=\"playbook_4ca114c5_ba00_4cd8_b923_729a2d9bf15d\" isExecutable=\"true\" name=\"playbook_4ca114c5_ba00_4cd8_b923_729a2d9bf15d\"\u003e\u003cdocumentation/\u003e\u003cstartEvent id=\"StartEvent_155asxm\"\u003e\u003coutgoing\u003eFlow_0wuog2x\u003c/outgoing\u003e\u003c/startEvent\u003e\u003cendEvent id=\"EndPoint_1\" resilient:documentation=\"End point\"\u003e\u003cincoming\u003eFlow_0o8vv55\u003c/incoming\u003e\u003c/endEvent\u003e\u003csequenceFlow id=\"Flow_0wuog2x\" sourceRef=\"StartEvent_155asxm\" targetRef=\"CallActivity_2\"/\u003e\u003ccallActivity calledElement=\"playbook_9e580fbd_5c66_4246_9ea4_e2379ea13ebf\" id=\"CallActivity_2\" name=\"test_sub_playbook\" resilient:type=\"sub-playbook\"\u003e\u003cextensionElements\u003e\u003cresilient:sub-playbook name=\"test_sub_playbook\" uuid=\"9e580fbd-5c66-4246-9ea4-e2379ea13ebf\"\u003e{\"inputs\":{\"6b934067-7a03-4765-a378-3df3a146a5ce\":{\"input_type\":\"static\",\"static_input\":{\"boolean_value\":true}}},\"pre_processing_script\":null,\"pre_processing_script_language\":null,\"result_name\":\"sub_pb_output\"}\u003c/resilient:sub-playbook\u003e\u003ccamunda:in source=\"RESILIENT_CONTEXT\" target=\"RESILIENT_CONTEXT\"/\u003e\u003c/extensionElements\u003e\u003cincoming\u003eFlow_0wuog2x\u003c/incoming\u003e\u003coutgoing\u003eFlow_0o8vv55\u003c/outgoing\u003e\u003c/callActivity\u003e\u003csequenceFlow id=\"Flow_0o8vv55\" sourceRef=\"CallActivity_2\" targetRef=\"EndPoint_1\"/\u003e\u003c/process\u003e\u003cbpmndi:BPMNDiagram id=\"BPMNDiagram_1\"\u003e\u003cbpmndi:BPMNPlane bpmnElement=\"playbook_4ca114c5_ba00_4cd8_b923_729a2d9bf15d\" id=\"BPMNPlane_1\"\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_0o8vv55\" id=\"Flow_0o8vv55_di\"\u003e\u003comgdi:waypoint x=\"567\" y=\"318\"/\u003e\u003comgdi:waypoint x=\"567\" y=\"420\"/\u003e\u003comgdi:waypoint x=\"655\" y=\"420\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Flow_0wuog2x\" id=\"Flow_0wuog2x_di\"\u003e\u003comgdi:waypoint x=\"621\" y=\"91\"/\u003e\u003comgdi:waypoint x=\"567\" y=\"91\"/\u003e\u003comgdi:waypoint x=\"567\" y=\"201\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNShape bpmnElement=\"StartEvent_155asxm\" id=\"StartEvent_155asxm_di\"\u003e\u003comgdc:Bounds height=\"52\" width=\"199.65\" x=\"621\" y=\"65\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"0\" width=\"90\" x=\"616\" y=\"100\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"EndPoint_1\" id=\"EndPoint_1_di\"\u003e\u003comgdc:Bounds height=\"52\" width=\"132.15\" x=\"655\" y=\"394\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"CallActivity_2\" id=\"CallActivity_2_di\"\u003e\u003comgdc:Bounds height=\"117\" width=\"196\" x=\"469.325\" y=\"200.5\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003c/bpmndi:BPMNPlane\u003e\u003c/bpmndi:BPMNDiagram\u003e\u003c/definitions\u003e"
        },
        "create_date": 1691091166564,
        "creator_principal": {
          "display_name": "Admin User",
          "id": 1,
          "name": "admin@example.com",
          "type": "user"
        },
        "deployment_id": "playbook_4ca114c5_ba00_4cd8_b923_729a2d9bf15d",
        "description": {
          "content": null,
          "format": "text"
        },
        "display_name": "test_rule_conditions",
        "export_key": "test_rule_conditions",
        "field_type_handle": "playbook_4ca114c5_ba00_4cd8_b923_729a2d9bf15d",
        "fields_type": {
          "actions": [],
          "display_name": "test_rule_conditions",
          "export_key": "playbook_4ca114c5_ba00_4cd8_b923_729a2d9bf15d",
          "fields": {},
          "for_actions": false,
          "for_custom_fields": false,
          "for_notifications": false,
          "for_workflows": false,
          "id": null,
          "parent_types": [
            "__playbook"
          ],
          "properties": {
            "can_create": false,
            "can_destroy": false,
            "for_who": []
          },
          "scripts": [],
          "tags": [],
          "type_id": 28,
          "type_name": "playbook_4ca114c5_ba00_4cd8_b923_729a2d9bf15d",
          "uuid": "94f0d225-6154-45d7-8a30-c903801f98cc"
        },
        "has_logical_errors": false,
        "id": 23,
        "is_deleted": false,
        "is_locked": false,
        "last_modified_principal": {
          "display_name": "Admin User",
          "id": 1,
          "name": "admin@example.com",
          "type": "user"
        },
        "last_modified_time": 1691096713243,
        "local_scripts": [],
        "name": "test_rule_conditions",
        "object_type": "qradar_reference_set",
        "status": "enabled",
        "tag": {
          "display_name": "Playbook_4ca114c5-ba00-4cd8-b923-729a2d9bf15d",
          "id": 33,
          "name": "playbook_4ca114c5_ba00_4cd8_b923_729a2d9bf15d",
          "type": "playbook",
          "uuid": "544da314-13df-4bc8-b115-1f10a2e05b18"
        },
        "tags": [],
        "type": "default",
        "uuid": "4ca114c5-ba00-4cd8-b923-729a2d9bf15d",
        "version": 15
      }
    ],
    "regulators": null,
    "roles": [],
    "scripts": [
      {
        "actions": [],
        "created_date": 1690921309788,
        "description": "",
        "enabled": false,
        "export_key": "handle output for playbook readme",
        "id": 35,
        "language": "python3",
        "last_modified_by": "admin@example.com",
        "last_modified_time": 1691004191548,
        "name": "handle output for playbook readme",
        "object_type": "incident",
        "playbook_handle": null,
        "programmatic_name": "handle_output_for_playbook_readme",
        "script_text": "incident.addNote(playbook.functions.results.output)\npass",
        "tags": [],
        "uuid": "9c3e685b-acf8-42fd-a1a8-021366d40f9d"
      }
    ],
    "server_version": {
      "build_number": 8803,
      "major": 49,
      "minor": 0,
      "version": "49.0.8803"
    },
    "tags": [],
    "task_order": [],
    "timeframes": null,
    "types": [],
    "workflows": [],
    "workspaces": []
  }
  