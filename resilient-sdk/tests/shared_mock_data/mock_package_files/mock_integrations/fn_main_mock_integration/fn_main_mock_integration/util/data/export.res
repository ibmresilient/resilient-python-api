{
  "action_order": [],
  "actions": [
    {
      "automations": [],
      "conditions": [
        {
          "evaluation_id": null,
          "field_name": null,
          "method": "object_added",
          "type": null,
          "value": null
        }
      ],
      "enabled": true,
      "export_key": "Mock: Auto Rule",
      "id": 18,
      "logic_type": "all",
      "message_destinations": [],
      "name": "Mock: Auto Rule",
      "object_type": "incident",
      "tags": [],
      "timeout_seconds": 86400,
      "type": 0,
      "uuid": "b63091d4-2a67-44df-b117-299061d8f65c",
      "view_items": [],
      "workflows": [
        "mock_workflow_one"
      ]
    },
    {
      "automations": [],
      "conditions": [],
      "enabled": true,
      "export_key": "Mock Manual Rule",
      "id": 14,
      "logic_type": "all",
      "message_destinations": [],
      "name": "Mock Manual Rule",
      "object_type": "artifact",
      "tags": [],
      "timeout_seconds": 86400,
      "type": 1,
      "uuid": "7f4830d2-ce93-4d77-8318-1801da57921f",
      "view_items": [],
      "workflows": [
        "mock_workflow_one"
      ]
    },
    {
      "automations": [],
      "conditions": [],
      "enabled": true,
      "export_key": "Mock Manual Rule Message Destination",
      "id": 15,
      "logic_type": "all",
      "message_destinations": [
        "fn_test_two"
      ],
      "name": "Mock Manual Rule Message Destination",
      "object_type": "incident",
      "tags": [],
      "timeout_seconds": 86400,
      "type": 1,
      "uuid": "32fc2626-bd73-43df-887b-01b21c508ee9",
      "view_items": [],
      "workflows": []
    },
    {
      "automations": [
        {
          "scripts_to_run": "Mock Incident Script",
          "type": "run_script",
          "value": null
        },
        {
          "tasks_to_create": [
            "mock_custom_task_one"
          ],
          "type": "create_task",
          "value": null
        },
        {
          "field": "mock_field_number",
          "operation": "set_field",
          "type": "modify_field",
          "type_id": "incident",
          "value": 123
        },
        {
          "tasks_to_create": [
            "mock_cusom_task__________two"
          ],
          "type": "create_task",
          "value": null
        },
        {
          "field": "mock_field_text",
          "operation": "set_field",
          "type": "modify_field",
          "type_id": "incident",
          "value": "asdf"
        }
      ],
      "conditions": [],
      "enabled": true,
      "export_key": "Mock Script Rule",
      "id": 16,
      "logic_type": "all",
      "message_destinations": [
        "fn_test_two"
      ],
      "name": "Mock Script Rule",
      "object_type": "incident",
      "tags": [],
      "timeout_seconds": 86400,
      "type": 1,
      "uuid": "e4a713e4-3017-48d5-9995-ee45e974204e",
      "view_items": [],
      "workflows": [
        "mock_workflow_one"
      ]
    },
    {
      "automations": [
        {
          "tasks_to_create": [
            "initial_triage",
            "mock_custom_task_one"
          ],
          "type": "create_task",
          "value": null
        }
      ],
      "conditions": [],
      "enabled": true,
      "export_key": "Mock Task Rule",
      "id": 17,
      "logic_type": "all",
      "message_destinations": [],
      "name": "Mock Task Rule",
      "object_type": "incident",
      "tags": [],
      "timeout_seconds": 86400,
      "type": 1,
      "uuid": "ce687e84-b44d-44ee-a914-8165b50e155e",
      "view_items": [],
      "workflows": []
    },
    {
      "automations": [],
      "conditions": [],
      "enabled": true,
      "export_key": "Run Mock Function One",
      "id": 19,
      "logic_type": "all",
      "message_destinations": [],
      "name": "Run Mock Function One",
      "object_type": "incident",
      "tags": [],
      "timeout_seconds": 86400,
      "type": 1,
      "uuid": "c2d82132-102f-42b9-83fb-fc472e47e6f1",
      "view_items": [],
      "workflows": [
        "mock_workflow_one"
      ]
    }
  ],
  "apps": [],
  "automatic_tasks": [
    {
      "associated_actions": null,
      "category_id": null,
      "date_source_handle": "incident.discovered_date",
      "deleted": false,
      "due_date_offset": 0,
      "due_date_units": null,
      "enabled": true,
      "export_key": "initial_triage",
      "form": null,
      "id": 0,
      "instructions": "Execute an initial triage of the incident. Focus on determining information such as \n\u003cul\u003e\n\u003cli\u003eis this an actual incident or false alarm, \u003c/li\u003e\n\u003cli\u003ethe scope and impact, \u003c/li\u003e\n\u003cli\u003e systems involved including applications, operating systems, and business and technical owners,\u003c/li\u003e\n\u003cli\u003eis the incident still ongoing, \u003c/li\u003e\n\u003cli\u003ehas confidential or personal data possibly been exposed or exfiltrated, \u003c/li\u003e\n\u003cli\u003ehas there been illegal activity, \u003c/li\u003e\n\u003cli\u003eare employees involved, \u003c/li\u003e\n\u003cli\u003ehave your communication systems been compromised. \u003c/li\u003e\n\u003c/ul\u003e\nAdd notes to this task capturing all of your activities and initial findings. Adjust the incident team membership to include the necessary individuals and add details to the incident description including logistics around regularly scheduled meetings, etc.\n\u003cbr /\u003e\u003cbr /\u003e\nNote: If criminal or inappropriate employee activity is involved you should consider ensuring that the appropriate evidence collection and preservation procedures are followed.",
      "name": "Initial Triage",
      "optional": false,
      "phase_id": "Engage",
      "programmatic_name": "initial_triage",
      "tags": [],
      "task_layout": [],
      "uuid": "2d261a8a-14c3-4f0f-a237-7c6a76bf82b1"
    },
    {
      "associated_actions": null,
      "category_id": null,
      "date_source_handle": "incident.discovered_date",
      "deleted": false,
      "due_date_offset": 0,
      "due_date_units": null,
      "enabled": true,
      "export_key": "mock_cusom_task__________two",
      "form": null,
      "id": 0,
      "instructions": "\u003cdiv class=\"rte\"\u003e\u003cdiv\u003eSample instruction s \u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316 here now \u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316\u003c/div\u003e\u003c/div\u003e",
      "name": "Mock Cusom Task \u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316 Two",
      "optional": false,
      "phase_id": "Mock Custom Phase Two",
      "programmatic_name": "mock_cusom_task__________two",
      "tags": [],
      "task_layout": [
        {
          "content": "mock_field_number",
          "element": "field",
          "field_type": "incident",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "mock_field_text",
          "element": "field",
          "field_type": "incident",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "mock_field_text_area",
          "element": "field",
          "field_type": "incident",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        }
      ],
      "uuid": "3a7c8b57-637b-4598-a729-98140ec71275"
    },
    {
      "associated_actions": null,
      "category_id": null,
      "date_source_handle": "incident.discovered_date",
      "deleted": false,
      "due_date_offset": 0,
      "due_date_units": null,
      "enabled": true,
      "export_key": "mock_custom_task_one",
      "form": null,
      "id": 0,
      "instructions": "\u003cdiv class=\"rte\"\u003e\u003cdiv\u003eSample instructions \u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316 \u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316 \u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316\u003c/div\u003e\u003c/div\u003e",
      "name": "Mock Custom Task One",
      "optional": false,
      "phase_id": "Mock Custom Phase One",
      "programmatic_name": "mock_custom_task_one",
      "tags": [],
      "task_layout": [
        {
          "content": "mock_field_number",
          "element": "field",
          "field_type": "incident",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        }
      ],
      "uuid": "df101758-75dd-46d3-b080-1f338fc088a2"
    }
  ],
  "export_date": 1624967473343,
  "export_format_version": 2,
  "fields": [
    {
      "allow_default_value": false,
      "blank_option": false,
      "calculated": false,
      "changeable": true,
      "chosen": false,
      "default_chosen_by_server": false,
      "deprecated": false,
      "export_key": "__function/mock_input_text_with_value_string",
      "hide_notification": false,
      "id": 255,
      "input_type": "textarea",
      "internal": false,
      "is_tracked": false,
      "name": "mock_input_text_with_value_string",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": null,
      "read_only": false,
      "rich_text": false,
      "tags": [],
      "templates": [
        {
          "id": 1,
          "name": "display_value_two",
          "template": {
            "content": "data value two  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
            "format": "text"
          },
          "uuid": "250a905e-e620-4e25-b2b8-77d123a1f21c"
        },
        {
          "id": 2,
          "name": "display_value_one",
          "template": {
            "content": "data value one  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
            "format": "text"
          },
          "uuid": "7b2ca17d-c591-4454-a0b8-5b65b97a441f"
        }
      ],
      "text": "mock_input_text_with_value_string",
      "tooltip": "a mock tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 11,
      "uuid": "866625eb-8b46-4cc9-b713-cdfa548a1189",
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
      "export_key": "__function/mock_input_date_time_picker",
      "hide_notification": false,
      "id": 256,
      "input_type": "datetimepicker",
      "internal": false,
      "is_tracked": false,
      "name": "mock_input_date_time_picker",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": null,
      "read_only": false,
      "rich_text": false,
      "tags": [],
      "templates": [],
      "text": "mock_input_date_time_picker",
      "tooltip": "a mock tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 11,
      "uuid": "92eb3b7a-8859-4846-81a3-2995aec74bdb",
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
      "export_key": "__function/mock_input_select",
      "hide_notification": false,
      "id": 257,
      "input_type": "select",
      "internal": false,
      "is_tracked": false,
      "name": "mock_input_select",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": null,
      "read_only": false,
      "rich_text": false,
      "tags": [],
      "templates": [],
      "text": "mock_input_select",
      "tooltip": "mock tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 11,
      "uuid": "b6dfde6d-7516-4509-a5a2-54e72df9e0cd",
      "values": [
        {
          "default": true,
          "enabled": true,
          "hidden": false,
          "label": "select one",
          "properties": null,
          "uuid": "0a30d6ad-914a-47b1-83bf-c5667dbee974",
          "value": 52
        },
        {
          "default": false,
          "enabled": true,
          "hidden": false,
          "label": "select two",
          "properties": null,
          "uuid": "7522822e-67bc-478e-b91d-7116b14ce2a5",
          "value": 53
        },
        {
          "default": false,
          "enabled": true,
          "hidden": false,
          "label": "select  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
          "properties": null,
          "uuid": "9f40a2b2-2318-4d73-8e48-4a447c70890c",
          "value": 54
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
      "export_key": "__function/mock_input_boolean",
      "hide_notification": false,
      "id": 258,
      "input_type": "boolean",
      "internal": false,
      "is_tracked": false,
      "name": "mock_input_boolean",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": null,
      "read_only": false,
      "rich_text": false,
      "tags": [],
      "templates": [],
      "text": "mock_input_boolean",
      "tooltip": "a mock tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 11,
      "uuid": "df7df8ba-cb65-4400-8290-070b155d28d4",
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
      "export_key": "__function/mock_input_text",
      "hide_notification": false,
      "id": 259,
      "input_type": "text",
      "internal": false,
      "is_tracked": false,
      "name": "mock_input_text",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": null,
      "read_only": false,
      "rich_text": false,
      "tags": [],
      "templates": [],
      "text": "mock_input_text",
      "tooltip": "a mock tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 11,
      "uuid": "e40b9d9e-7ca1-45bc-913b-ce2a77e9b687",
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
      "export_key": "__function/mock_input_date_picker",
      "hide_notification": false,
      "id": 260,
      "input_type": "datepicker",
      "internal": false,
      "is_tracked": false,
      "name": "mock_input_date_picker",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": null,
      "read_only": false,
      "rich_text": false,
      "tags": [],
      "templates": [],
      "text": "mock_input_date_picker",
      "tooltip": "a mock tooltip \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 11,
      "uuid": "01147ebf-ce3d-4cfb-814b-16145af4e511",
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
      "export_key": "__function/mock_input_number",
      "hide_notification": false,
      "id": 261,
      "input_type": "number",
      "internal": false,
      "is_tracked": false,
      "name": "mock_input_number",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": null,
      "read_only": false,
      "required": "always",
      "rich_text": false,
      "tags": [],
      "templates": [],
      "text": "mock_input_number",
      "tooltip": "a mock tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 11,
      "uuid": "49f10172-309a-4829-a5fe-1de71cdb4efb",
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
      "export_key": "__function/mock_input_multiselect",
      "hide_notification": false,
      "id": 262,
      "input_type": "multiselect",
      "internal": false,
      "is_tracked": false,
      "name": "mock_input_multiselect",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": null,
      "read_only": false,
      "rich_text": false,
      "tags": [],
      "templates": [],
      "text": "mock_input_multiselect",
      "tooltip": "a mock input tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 11,
      "uuid": "69dc0e78-a74b-4ccc-8d82-33b51780a569",
      "values": [
        {
          "default": true,
          "enabled": true,
          "hidden": false,
          "label": "value one",
          "properties": null,
          "uuid": "8b8b22d4-b20c-4d10-abac-a65211a5b9cd",
          "value": 55
        },
        {
          "default": true,
          "enabled": true,
          "hidden": false,
          "label": "value two",
          "properties": null,
          "uuid": "bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e",
          "value": 56
        },
        {
          "default": false,
          "enabled": true,
          "hidden": false,
          "label": "value  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
          "properties": null,
          "uuid": "c0e1c417-00b8-4146-8ca9-248215be0efa",
          "value": 57
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
      "export_key": "incident/mock_field_text_area",
      "hide_notification": false,
      "id": 247,
      "input_type": "textarea",
      "internal": false,
      "is_tracked": false,
      "name": "mock_field_text_area",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": "properties",
      "read_only": false,
      "required": "close",
      "rich_text": true,
      "tags": [],
      "templates": [],
      "text": "Mock: Field Text Area  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "tooltip": "a tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 0,
      "uuid": "d7cc8d00-1d54-4b3a-af0d-236ef0566751",
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
      "export_key": "incident/mock_field_text",
      "hide_notification": false,
      "id": 248,
      "input_type": "text",
      "internal": false,
      "is_tracked": false,
      "name": "mock_field_text",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": "properties",
      "read_only": false,
      "rich_text": false,
      "tags": [],
      "templates": [],
      "text": "Mock: Field Text",
      "tooltip": "a mock tooltip",
      "type_id": 0,
      "uuid": "f63a85ca-0e50-4504-81ab-c45d16494d0c",
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
      "export_key": "incident/mock_field_number",
      "hide_notification": false,
      "id": 249,
      "input_type": "number",
      "internal": false,
      "is_tracked": false,
      "name": "mock_field_number",
      "operation_perms": {},
      "operations": [],
      "placeholder": "",
      "prefix": "properties",
      "read_only": false,
      "rich_text": false,
      "tags": [],
      "templates": [],
      "text": "Mock:  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d field number",
      "tooltip": "a mock tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "type_id": 0,
      "uuid": "2653024f-9abb-4440-aa61-cb3f6262f6ee",
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
      "created_date": 1624967209442,
      "description": {
        "content": "A mock description of \u0027A Mock Function with No Unicode Characters in Name\u0027 with unicode:  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
        "format": "text"
      },
      "destination_handle": "fn_main_mock_integration",
      "display_name": "A Mock Function with :: No Unicode Characters !@#$%^\u0026*())))in Name",
      "export_key": "a_mock_function_with_no_unicode_characters_in_name",
      "id": 1,
      "last_modified_by": {
        "display_name": "Local Integration Server",
        "id": 4,
        "name": "ad261c1f-f1cc-4115-bbce-a151f88bac5e",
        "type": "apikey"
      },
      "last_modified_time": 1624967209484,
      "name": "a_mock_function_with_no_unicode_characters_in_name",
      "tags": [],
      "uuid": "acd10fc9-9c81-456b-a141-bb0c2279a721",
      "version": 1,
      "view_items": [
        {
          "content": "e40b9d9e-7ca1-45bc-913b-ce2a77e9b687",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        }
      ],
      "workflows": []
    },
    {
      "created_date": 1624967209513,
      "description": {
        "content": "mock function \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d three description",
        "format": "text"
      },
      "destination_handle": "fn_main_mock_integration",
      "display_name": "mock function \u0e25 three",
      "export_key": "mock_function__three",
      "id": 2,
      "last_modified_by": {
        "display_name": "Local Integration Server",
        "id": 4,
        "name": "ad261c1f-f1cc-4115-bbce-a151f88bac5e",
        "type": "apikey"
      },
      "last_modified_time": 1624967209641,
      "name": "mock_function__three",
      "tags": [],
      "uuid": "0c7fd5a3-b67f-47f5-bda4-76ff3f60dd69",
      "version": 1,
      "view_items": [
        {
          "content": "df7df8ba-cb65-4400-8290-070b155d28d4",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        }
      ],
      "workflows": []
    },
    {
      "created_date": 1624967209672,
      "description": {
        "content": "A mock description of mock_function_one with unicode:  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
        "format": "text"
      },
      "destination_handle": "fn_main_mock_integration",
      "display_name": "mock_function_one",
      "export_key": "mock_function_one",
      "id": 3,
      "last_modified_by": {
        "display_name": "Local Integration Server",
        "id": 4,
        "name": "ad261c1f-f1cc-4115-bbce-a151f88bac5e",
        "type": "apikey"
      },
      "last_modified_time": 1624967209707,
      "name": "mock_function_one",
      "tags": [],
      "uuid": "9b180887-4ff6-4d13-82a6-cb0a5d8718f1",
      "version": 1,
      "view_items": [
        {
          "content": "01147ebf-ce3d-4cfb-814b-16145af4e511",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "92eb3b7a-8859-4846-81a3-2995aec74bdb",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "49f10172-309a-4829-a5fe-1de71cdb4efb",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "e40b9d9e-7ca1-45bc-913b-ce2a77e9b687",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "866625eb-8b46-4cc9-b713-cdfa548a1189",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "b6dfde6d-7516-4509-a5a2-54e72df9e0cd",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "df7df8ba-cb65-4400-8290-070b155d28d4",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "69dc0e78-a74b-4ccc-8d82-33b51780a569",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        }
      ],
      "workflows": [
        {
          "actions": [],
          "description": null,
          "name": "mock workflow  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d two",
          "object_type": "artifact",
          "programmatic_name": "mock_workflow_two",
          "tags": [],
          "uuid": null,
          "workflow_id": 2
        },
        {
          "actions": [],
          "description": null,
          "name": "Mock Workflow One",
          "object_type": "incident",
          "programmatic_name": "mock_workflow_one",
          "tags": [],
          "uuid": null,
          "workflow_id": 1
        }
      ]
    },
    {
      "created_date": 1624967209728,
      "description": {
        "content": "a  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d description of  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d mock function two",
        "format": "text"
      },
      "destination_handle": "fn_main_mock_integration",
      "display_name": "mock function  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d two",
      "export_key": "mock_function_two",
      "id": 4,
      "last_modified_by": {
        "display_name": "Local Integration Server",
        "id": 4,
        "name": "ad261c1f-f1cc-4115-bbce-a151f88bac5e",
        "type": "apikey"
      },
      "last_modified_time": 1624967209765,
      "name": "mock_function_two",
      "tags": [],
      "uuid": "90be4dd8-59a0-4791-82e9-df5d7e86edcb",
      "version": 1,
      "view_items": [
        {
          "content": "df7df8ba-cb65-4400-8290-070b155d28d4",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "49f10172-309a-4829-a5fe-1de71cdb4efb",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        },
        {
          "content": "e40b9d9e-7ca1-45bc-913b-ce2a77e9b687",
          "element": "field_uuid",
          "field_type": "__function",
          "show_if": null,
          "show_link_header": false,
          "step_label": null
        }
      ],
      "workflows": [
        {
          "actions": [],
          "description": null,
          "name": "mock workflow  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d two",
          "object_type": "artifact",
          "programmatic_name": "mock_workflow_two",
          "tags": [],
          "uuid": null,
          "workflow_id": 2
        }
      ]
    }
  ],
  "geos": null,
  "groups": null,
  "id": 1,
  "inbound_destinations": [],
  "inbound_mailboxes": null,
  "incident_artifact_types": [
    {
      "default_scan_option": "unsupported",
      "desc": "\u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316 \u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316asdf \u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316",
      "enabled": true,
      "export_key": "mock_artifact_2",
      "file": false,
      "id": 0,
      "multi_aware": true,
      "name": "Mock Artifact 2 \u330e \u330f \u3310 \u3311 \u3312 \u3313 \u3314 \u3315 \u3316",
      "parse_as_csv": false,
      "programmatic_name": "mock_artifact_2",
      "reg_exp": null,
      "system": false,
      "tags": [],
      "use_for_relationships": true,
      "uuid": "0405a242-872b-4d85-9e79-70a26a9d7462",
      "version": 0
    },
    {
      "default_scan_option": "unsupported",
      "desc": "A mock description of this Artifact type",
      "enabled": true,
      "export_key": "mock_artifact_type_one",
      "file": false,
      "id": 0,
      "multi_aware": true,
      "name": "Mock Artifact Type One",
      "parse_as_csv": false,
      "programmatic_name": "mock_artifact_type_one",
      "reg_exp": null,
      "system": false,
      "tags": [],
      "use_for_relationships": true,
      "uuid": "1997c7d5-7c81-49f0-91d3-b0b6cb190ca3",
      "version": 0
    }
  ],
  "incident_types": [
    {
      "create_date": 1624967471551,
      "description": "Customization Packages (internal)",
      "enabled": false,
      "export_key": "Customization Packages (internal)",
      "hidden": false,
      "id": 0,
      "name": "Customization Packages (internal)",
      "parent_id": null,
      "system": false,
      "update_date": 1624967471551,
      "uuid": "bfeec2d4-3770-11e8-ad39-4a0004044aa0"
    }
  ],
  "industries": null,
  "layouts": [],
  "locale": null,
  "message_destinations": [
    {
      "api_keys": [
        "ad261c1f-f1cc-4115-bbce-a151f88bac5e"
      ],
      "destination_type": 0,
      "expect_ack": true,
      "export_key": "fn_main_mock_integration",
      "name": "fn_main_mock_integration",
      "programmatic_name": "fn_main_mock_integration",
      "tags": [],
      "users": [],
      "uuid": "f36c49bf-df8c-46f3-a4cd-9a0cba961f92"
    },
    {
      "api_keys": [
        "ad261c1f-f1cc-4115-bbce-a151f88bac5e"
      ],
      "destination_type": 0,
      "expect_ack": true,
      "export_key": "fn_test_two",
      "name": "fn_test_two",
      "programmatic_name": "fn_test_two",
      "tags": [],
      "users": [],
      "uuid": "fb3f8e6a-d939-4594-addf-6d69ec2381bf"
    }
  ],
  "notifications": null,
  "overrides": [],
  "phases": [
    {
      "enabled": true,
      "export_key": "Engage",
      "id": 0,
      "name": "Engage",
      "order": 1,
      "perms": null,
      "tags": [],
      "uuid": "ed053e3a-2d6d-47e1-8240-844ed93d4893"
    },
    {
      "enabled": true,
      "export_key": "Mock Custom Phase One",
      "id": 0,
      "name": "Mock Custom Phase One",
      "order": 6,
      "perms": null,
      "tags": [],
      "uuid": "187b290c-19b5-4f29-97e8-16e9ff604a72"
    },
    {
      "enabled": true,
      "export_key": "Mock Custom Phase Two",
      "id": 0,
      "name": "Mock Custom Phase Two",
      "order": 7,
      "perms": null,
      "tags": [],
      "uuid": "44bfae00-280d-40db-9e14-124bd86002e5"
    }
  ],
  "regulators": null,
  "roles": [],
  "scripts": [
    {
      "actions": [],
      "created_date": 1624967208644,
      "description": "",
      "enabled": false,
      "export_key": "Mock Incident Script",
      "id": 2,
      "language": "python",
      "last_modified_by": "ad261c1f-f1cc-4115-bbce-a151f88bac5e",
      "last_modified_time": 1624967208664,
      "name": "Mock Incident Script",
      "object_type": "incident",
      "playbook_handle": null,
      "programmatic_name": "mock_incident_script",
      "script_text": "log.info(\"Run this\")",
      "tags": [],
      "uuid": "52e88afe-0ca8-4bac-823f-980bc8ba2931"
    },
    {
      "actions": [],
      "created_date": 1624967208692,
      "description": "a sample Artifact script",
      "enabled": false,
      "export_key": "Mock Script One",
      "id": 3,
      "language": "python",
      "last_modified_by": "ad261c1f-f1cc-4115-bbce-a151f88bac5e",
      "last_modified_time": 1624967208709,
      "name": "Mock Script One",
      "object_type": "artifact",
      "playbook_handle": null,
      "programmatic_name": "mock_script_one",
      "script_text": "log.info(\"Print this message\")",
      "tags": [],
      "uuid": "d73d75f5-d8cf-4c00-8110-c5bf258b51da"
    }
  ],
  "server_version": {
    "build_number": 6783,
    "major": 41,
    "minor": 0,
    "version": "41.0.6783"
  },
  "tags": [],
  "task_order": [],
  "timeframes": null,
  "types": [
    {
      "actions": [],
      "display_name": "Mock: Data Table  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "export_key": "mock_data_table",
      "fields": {
        "mock_col_one": {
          "allow_default_value": false,
          "blank_option": false,
          "calculated": false,
          "changeable": true,
          "chosen": false,
          "default_chosen_by_server": false,
          "deprecated": false,
          "export_key": "mock_data_table/mock_col_one",
          "hide_notification": false,
          "id": 251,
          "input_type": "text",
          "internal": false,
          "is_tracked": false,
          "name": "mock_col_one",
          "operation_perms": {},
          "operations": [],
          "order": 0,
          "placeholder": "",
          "prefix": null,
          "read_only": false,
          "rich_text": false,
          "tags": [],
          "templates": [],
          "text": "mock col one",
          "tooltip": "a tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
          "type_id": 1000,
          "uuid": "83a3fea3-ddfd-46ee-82df-a0070e2476d9",
          "values": [],
          "width": 246
        },
        "mok_col_two": {
          "allow_default_value": false,
          "blank_option": false,
          "calculated": false,
          "changeable": true,
          "chosen": false,
          "default_chosen_by_server": false,
          "deprecated": false,
          "export_key": "mock_data_table/mok_col_two",
          "hide_notification": false,
          "id": 252,
          "input_type": "number",
          "internal": false,
          "is_tracked": false,
          "name": "mok_col_two",
          "operation_perms": {},
          "operations": [],
          "order": 1,
          "placeholder": "",
          "prefix": null,
          "read_only": false,
          "rich_text": false,
          "tags": [],
          "templates": [],
          "text": "mock  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d col two",
          "tooltip": "tooltip  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
          "type_id": 1000,
          "uuid": "b364709b-b804-4ce2-8c04-d451966b0a7f",
          "values": [],
          "width": 456
        }
      },
      "for_actions": false,
      "for_custom_fields": false,
      "for_notifications": false,
      "for_workflows": false,
      "id": null,
      "parent_types": [
        "incident"
      ],
      "properties": {
        "can_create": false,
        "can_destroy": false,
        "for_who": []
      },
      "scripts": [],
      "tags": [],
      "type_id": 8,
      "type_name": "mock_data_table",
      "uuid": "66cc5d9f-7c9a-42e7-991e-d8e5288c01ba"
    }
  ],
  "workflows": [
    {
      "actions": [],
      "content": {
        "version": 1,
        "workflow_id": "mock_workflow_two",
        "xml": "\u003c?xml version=\"1.0\" encoding=\"UTF-8\"?\u003e\u003cdefinitions xmlns=\"http://www.omg.org/spec/BPMN/20100524/MODEL\" xmlns:bpmndi=\"http://www.omg.org/spec/BPMN/20100524/DI\" xmlns:omgdc=\"http://www.omg.org/spec/DD/20100524/DC\" xmlns:omgdi=\"http://www.omg.org/spec/DD/20100524/DI\" xmlns:resilient=\"http://resilient.ibm.com/bpmn\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" targetNamespace=\"http://www.camunda.org/test\"\u003e\u003cprocess id=\"mock_workflow_two\" isExecutable=\"true\" name=\"mock workflow  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d two\"\u003e\u003cdocumentation\u003ea descirption of  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d mock workflow  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d two\u003c/documentation\u003e\u003cstartEvent id=\"StartEvent_155asxm\"\u003e\u003coutgoing\u003eSequenceFlow_0qvmb7u\u003c/outgoing\u003e\u003c/startEvent\u003e\u003cserviceTask id=\"ServiceTask_1gf1ya4\" name=\"mock_function_one\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"9b180887-4ff6-4d13-82a6-cb0a5d8718f1\"\u003e{\"inputs\":{\"b6dfde6d-7516-4509-a5a2-54e72df9e0cd\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"select_value\":\"0a30d6ad-914a-47b1-83bf-c5667dbee974\"}},\"69dc0e78-a74b-4ccc-8d82-33b51780a569\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[\"8b8b22d4-b20c-4d10-abac-a65211a5b9cd\",\"bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e\"]}}},\"post_processing_script\":\"# a mock post  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d script of  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d function one\\n\\nif True:\\n  incident.addNote(\\\"this note was added \\\")\",\"result_name\":\"mock_output_of_function_one\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eSequenceFlow_0qvmb7u\u003c/incoming\u003e\u003coutgoing\u003eSequenceFlow_1efekzp\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003cserviceTask id=\"ServiceTask_0uxjjuo\" name=\"mock function  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d ...\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"90be4dd8-59a0-4791-82e9-df5d7e86edcb\"\u003e{\"inputs\":{},\"pre_processing_script\":\"# mock pre script of function  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d two:\\n\\ninputs.mock_input_boolean = False\\ninputs.mock_input_number = 1001\\ninputs.mock_input_text = u\\\" \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d ramdom text\\\"\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eSequenceFlow_1efekzp\u003c/incoming\u003e\u003coutgoing\u003eSequenceFlow_0a5l4on\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003csequenceFlow id=\"SequenceFlow_0qvmb7u\" sourceRef=\"StartEvent_155asxm\" targetRef=\"ServiceTask_1gf1ya4\"/\u003e\u003csequenceFlow id=\"SequenceFlow_1efekzp\" sourceRef=\"ServiceTask_1gf1ya4\" targetRef=\"ServiceTask_0uxjjuo\"/\u003e\u003cendEvent id=\"EndEvent_0s81h2i\"\u003e\u003cincoming\u003eSequenceFlow_0a5l4on\u003c/incoming\u003e\u003c/endEvent\u003e\u003csequenceFlow id=\"SequenceFlow_0a5l4on\" sourceRef=\"ServiceTask_0uxjjuo\" targetRef=\"EndEvent_0s81h2i\"/\u003e\u003c/process\u003e\u003cbpmndi:BPMNDiagram id=\"BPMNDiagram_1\"\u003e\u003cbpmndi:BPMNPlane bpmnElement=\"undefined\" id=\"BPMNPlane_1\"\u003e\u003cbpmndi:BPMNShape bpmnElement=\"StartEvent_155asxm\" id=\"StartEvent_155asxm_di\"\u003e\u003comgdc:Bounds height=\"36\" width=\"36\" x=\"74\" y=\"188\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"0\" width=\"90\" x=\"69\" y=\"223\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_1gf1ya4\" id=\"ServiceTask_1gf1ya4_di\"\u003e\u003comgdc:Bounds height=\"80\" width=\"100\" x=\"241\" y=\"166\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_0uxjjuo\" id=\"ServiceTask_0uxjjuo_di\"\u003e\u003comgdc:Bounds height=\"80\" width=\"100\" x=\"479\" y=\"166\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"SequenceFlow_0qvmb7u\" id=\"SequenceFlow_0qvmb7u_di\"\u003e\u003comgdi:waypoint x=\"110\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003comgdi:waypoint x=\"241\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"13\" width=\"0\" x=\"175.5\" y=\"184.5\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"SequenceFlow_1efekzp\" id=\"SequenceFlow_1efekzp_di\"\u003e\u003comgdi:waypoint x=\"341\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003comgdi:waypoint x=\"479\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"13\" width=\"0\" x=\"410\" y=\"184.5\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNShape bpmnElement=\"EndEvent_0s81h2i\" id=\"EndEvent_0s81h2i_di\"\u003e\u003comgdc:Bounds height=\"36\" width=\"36\" x=\"726\" y=\"188\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"13\" width=\"0\" x=\"744\" y=\"227\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"SequenceFlow_0a5l4on\" id=\"SequenceFlow_0a5l4on_di\"\u003e\u003comgdi:waypoint x=\"579\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003comgdi:waypoint x=\"726\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"13\" width=\"0\" x=\"652.5\" y=\"184.5\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNEdge\u003e\u003c/bpmndi:BPMNPlane\u003e\u003c/bpmndi:BPMNDiagram\u003e\u003c/definitions\u003e"
      },
      "content_version": 1,
      "description": "a descirption of  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d mock workflow  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d two",
      "export_key": "mock_workflow_two",
      "last_modified_by": "ad261c1f-f1cc-4115-bbce-a151f88bac5e",
      "last_modified_time": 1624967210498,
      "name": "mock workflow  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d two",
      "object_type": "artifact",
      "programmatic_name": "mock_workflow_two",
      "tags": [],
      "uuid": "fef372ed-3410-413b-b01b-9b34e31b8005",
      "workflow_id": 2
    },
    {
      "actions": [],
      "content": {
        "version": 2,
        "workflow_id": "mock_workflow_one",
        "xml": "\u003c?xml version=\"1.0\" encoding=\"UTF-8\"?\u003e\u003cdefinitions xmlns=\"http://www.omg.org/spec/BPMN/20100524/MODEL\" xmlns:bpmndi=\"http://www.omg.org/spec/BPMN/20100524/DI\" xmlns:omgdc=\"http://www.omg.org/spec/DD/20100524/DC\" xmlns:omgdi=\"http://www.omg.org/spec/DD/20100524/DI\" xmlns:resilient=\"http://resilient.ibm.com/bpmn\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" targetNamespace=\"http://www.camunda.org/test\"\u003e\u003cprocess id=\"mock_workflow_one\" isExecutable=\"true\" name=\"Mock Workflow One\"\u003e\u003cdocumentation\u003ea description of mock workflow one  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d\u003c/documentation\u003e\u003cstartEvent id=\"StartEvent_155asxm\"\u003e\u003coutgoing\u003eSequenceFlow_1q8wygd\u003c/outgoing\u003e\u003c/startEvent\u003e\u003cserviceTask id=\"ServiceTask_1cpn7cb\" name=\"mock_function_one\" resilient:type=\"function\"\u003e\u003cextensionElements\u003e\u003cresilient:function uuid=\"9b180887-4ff6-4d13-82a6-cb0a5d8718f1\"\u003e{\"inputs\":{\"866625eb-8b46-4cc9-b713-cdfa548a1189\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"text_content_value\":{\"format\":\"text\",\"content\":\"data value one  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d\"}}},\"b6dfde6d-7516-4509-a5a2-54e72df9e0cd\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[],\"select_value\":\"7522822e-67bc-478e-b91d-7116b14ce2a5\"}},\"df7df8ba-cb65-4400-8290-070b155d28d4\":{\"input_type\":\"static\",\"static_input\":{\"boolean_value\":true,\"multiselect_value\":[]}},\"69dc0e78-a74b-4ccc-8d82-33b51780a569\":{\"input_type\":\"static\",\"static_input\":{\"multiselect_value\":[\"8b8b22d4-b20c-4d10-abac-a65211a5b9cd\",\"bf8e34a8-79aa-4ec4-b4c9-b8f1f0f7135e\"]}}},\"post_processing_script\":\"# post process of mock  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d workflow two\\n\\nincident.addNote(u\\\" \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d\\\")\",\"pre_processing_script\":\"# A mock pre-process script for mock_workflow_one\\n\\ninputs.mock_input_number = 123\\ninputs.mock_input_boolean = True\\ninputs.mock_input_text = \\\"abc  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d abc\\\"\",\"pre_processing_script_language\":\"python\",\"result_name\":\"output_of_mock_function_one\"}\u003c/resilient:function\u003e\u003c/extensionElements\u003e\u003cincoming\u003eSequenceFlow_1q8wygd\u003c/incoming\u003e\u003coutgoing\u003eSequenceFlow_0zyh9xo\u003c/outgoing\u003e\u003c/serviceTask\u003e\u003csequenceFlow id=\"SequenceFlow_1q8wygd\" sourceRef=\"StartEvent_155asxm\" targetRef=\"ServiceTask_1cpn7cb\"/\u003e\u003cendEvent id=\"EndEvent_09pyeky\"\u003e\u003cincoming\u003eSequenceFlow_0zyh9xo\u003c/incoming\u003e\u003c/endEvent\u003e\u003csequenceFlow id=\"SequenceFlow_0zyh9xo\" sourceRef=\"ServiceTask_1cpn7cb\" targetRef=\"EndEvent_09pyeky\"/\u003e\u003ctextAnnotation id=\"TextAnnotation_1kxxiyt\"\u003e\u003ctext\u003eStart your workflow here\u003c/text\u003e\u003c/textAnnotation\u003e\u003cassociation id=\"Association_1seuj48\" sourceRef=\"StartEvent_155asxm\" targetRef=\"TextAnnotation_1kxxiyt\"/\u003e\u003c/process\u003e\u003cbpmndi:BPMNDiagram id=\"BPMNDiagram_1\"\u003e\u003cbpmndi:BPMNPlane bpmnElement=\"undefined\" id=\"BPMNPlane_1\"\u003e\u003cbpmndi:BPMNShape bpmnElement=\"StartEvent_155asxm\" id=\"StartEvent_155asxm_di\"\u003e\u003comgdc:Bounds height=\"36\" width=\"36\" x=\"162\" y=\"188\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"0\" width=\"90\" x=\"157\" y=\"223\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNShape bpmnElement=\"TextAnnotation_1kxxiyt\" id=\"TextAnnotation_1kxxiyt_di\"\u003e\u003comgdc:Bounds height=\"30\" width=\"100\" x=\"99\" y=\"254\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"Association_1seuj48\" id=\"Association_1seuj48_di\"\u003e\u003comgdi:waypoint x=\"169\" xsi:type=\"omgdc:Point\" y=\"220\"/\u003e\u003comgdi:waypoint x=\"153\" xsi:type=\"omgdc:Point\" y=\"254\"/\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNShape bpmnElement=\"ServiceTask_1cpn7cb\" id=\"ServiceTask_1cpn7cb_di\"\u003e\u003comgdc:Bounds height=\"80\" width=\"100\" x=\"514\" y=\"166\"/\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"SequenceFlow_1q8wygd\" id=\"SequenceFlow_1q8wygd_di\"\u003e\u003comgdi:waypoint x=\"198\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003comgdi:waypoint x=\"514\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"13\" width=\"90\" x=\"311\" y=\"184.5\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNEdge\u003e\u003cbpmndi:BPMNShape bpmnElement=\"EndEvent_09pyeky\" id=\"EndEvent_09pyeky_di\"\u003e\u003comgdc:Bounds height=\"36\" width=\"36\" x=\"940\" y=\"188\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"13\" width=\"90\" x=\"913\" y=\"227\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNShape\u003e\u003cbpmndi:BPMNEdge bpmnElement=\"SequenceFlow_0zyh9xo\" id=\"SequenceFlow_0zyh9xo_di\"\u003e\u003comgdi:waypoint x=\"614\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003comgdi:waypoint x=\"940\" xsi:type=\"omgdc:Point\" y=\"206\"/\u003e\u003cbpmndi:BPMNLabel\u003e\u003comgdc:Bounds height=\"13\" width=\"90\" x=\"732\" y=\"184.5\"/\u003e\u003c/bpmndi:BPMNLabel\u003e\u003c/bpmndi:BPMNEdge\u003e\u003c/bpmndi:BPMNPlane\u003e\u003c/bpmndi:BPMNDiagram\u003e\u003c/definitions\u003e"
      },
      "content_version": 2,
      "description": "a description of mock workflow one  \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d \u0e25 \u0e26 \u0e27 \u0e28 \u0e29 \u0e2a \u0e2b \u0e2c \u0e2d",
      "export_key": "mock_workflow_one",
      "last_modified_by": "admin@example.com",
      "last_modified_time": 1624967264324,
      "name": "Mock Workflow One",
      "object_type": "incident",
      "programmatic_name": "mock_workflow_one",
      "tags": [],
      "uuid": "127ae053-c26f-43b7-8b5a-198720dbf202",
      "workflow_id": 1
    }
  ],
  "workspaces": []
}
