# -*- coding: utf-8 -*-
# (c) Copyright IBM Corp. 2010. 2025. All Rights Reserved.
# pragma pylint: disable=line-too-long, wrong-import-order

from typing import Union
from . import constants


def multiline_output(output_list: list, prefix: Union[str, None]=">>>", example: str=None) -> None:
    """Generalized method for presenting narrative data to track the sequence of data entry to the screen

    :param output_list: list of text strings to present
    :type output_list: list
    :param prefix: prefix for first line to give the section more visibility, defaults to ">>>"
    :type prefix: Union[str, None], optional
    :param example: example data to help in data entry, defaults to None
    :type example: str, optional
    """

    print("\n")
    if prefix:
        print(prefix, end=" ")

    output = "\n".join(output_list)
    if example:
        output = f"{output} Ex: {example}"

    print(output)

def prompt_input(prompt: Union[str, list],
                 multiline=False,
                 default:str =None,
                 example:str =None,
                 choices: list=None,
                 multi_select=False,
                 required=True) -> Union[str, list]:
    """common method for presenting prompt data and wait for and parse the results. If there are
        choices presented, the result is compared to the choices for correctness. If the prompt is
        required, prompts will continue until a (correct) response is parsed.

    :param prompt: prompt(s) to display before waiting for user input
    :type prompt: Union[str, list]
    :param multiline: if True, multiline data is enabled, defaults to False
    :type multiline: bool, optional
    :param default: if set an empty response will return the default value, defaults to None
    :type default: str, optional
    :param example: if present an example is shown in the prompt, defaults to None
    :type example: str, optional
    :param choices: if present numbered choices are presented, defaults to None
    :type choices: list, optional
    :param multi_select: if true, a comma separated list of choices is enabled, defaults to False
    :type multi_select: bool, optional
    :param required: if True, prompting will continue if no data entry is made, defaults to True
    :type required: bool, optional
    :return: the response(s) made by the user
    :rtype: Union[str, list]
    """

    multiline_prompt = "\n".join(prompt) if isinstance(prompt, list) else prompt
    if required:
        multiline_prompt = f"{multiline_prompt} *required*"

    if example:
        multiline_prompt = f"{multiline_prompt}\nEx: {example}"

    if choices:
        ndx = 1
        choice_list = []
        for choice in choices:
            choice_list.append(f"\n{ndx}) {choice}")
            ndx += 1

        multiline_prompt = f"{multiline_prompt}\nChoices: {', '.join(choice_list)}"

        if default:
            multiline_prompt = f"{multiline_prompt}\nDefault: {default} (Return/Enter selects the default)"
        multiline_prompt = f"{multiline_prompt}\nEnter Choice"
    else:
        if default:
            multiline_prompt = f"{multiline_prompt}\nDefault: {default} (Return/Enter selects the default)"
        multiline_prompt = f"{multiline_prompt}\nEnter Input"

    if not required and not default:
        multiline_prompt = f"{multiline_prompt} {constants.END_WITH_EMPTY_LINE}"

    # continue until the required data is entered. choices are parsed and default values used as needed
    while True:
        lines = get_input(f"\n{multiline_prompt}: ", multiline=multiline)

        if not lines and default:
            lines = [default]
            break

        if lines and choices:
            choice_results = parse_choices(lines[0], choices, multi_select=multi_select)
            if isinstance(choice_results, bool) or choice_results:
                return choice_results
        # confirm input and re-ask if input is required
        elif not lines and required:
            print_error("Response is required.")
        else:
            break

    return "\n".join(lines) if lines else None

def parse_choices(input: str, choices: list, multi_select: bool=None) -> list:
    """parse through the numbered choices made and return the original value presented.
        For example, if choices are A, B, C, they are presented to the user as: 1) A 2) B 3) B.

    :param input_list: responses from the user, ex: '1' or '2,3'
    :type input_list: str
    :param choices: list of choices
    :type choices: list
    :param multi_select: if true, more than one choice can be made, defaults to None
    :type multi_select: bool, optional
    :return: the choice(s) to return
    :rtype: list
    """

    results = []
    error_msg = f"Choose a number from 1 to {len(choices)}"
    # replace the index with value
    if multi_select:
        item_list = separate_multiple(input)
        for item in item_list:
            result = _parse_choice(item, choices)
            if not result:
                print(error_msg)
                return []
            results.append(result)
    else:
        results = _parse_choice(input, choices)
        if results is None:
            print(error_msg)
            return []

    return results

def _parse_choice(item: str, choices: list) -> Union[str, None]:
    """internal method for parsing one item value against the list of choices.
        If a prompt is multi-select, this method is called multiple times for each
        comma separated response

    :param item: selection value, ex. 1
    :type item: str
    :param choices: list of choices
    :type choices: list
    :return: matching choice from the choice list. None if no match
    :rtype: Union[str, None]
    """
    result = None
    try:
        ndx = int(item)
    except ValueError:
        ndx = 0
    if 0 < ndx <= len(choices):
        result = choices[ndx-1]

    return result

def get_input(prompt: str, multiline: bool=False) -> list:
    """common method for getting user input

    :param prompt: message to present before waiting for user input
    :type prompt: str
    :param multiline: if true multi line input is allowed, ending with an empty input line, defaults to False
    :type multiline: bool, optional
    :return: all the user data collected
    :rtype: list
    """
    lines = []

    line = input(prompt)
    while line:
        lines.append(line)
        if not multiline:
            break

        line = input()

    return lines

def make_another(section_list: Union[list, bool], default: str="", extra_char: Union[str, None]=" ") -> str:
    """common method to add the 'another' string when looping through a list of one or more inputs.
        Ex. first header prompt doesn't use this pronoun, but subsequent prompts will have it added in

    :param section_list: list to process, used to know if first time through. Could be boolean also
    :type section_list: list
    :param default: default value to use when section_list is empty
    :type default: str, optional
    :param extra_char: sometimes a space is needed for the sentence structure, defaults to " "
    :type extra_char: Union[str, None], optional
    :return: 'another' or 'another '
    :rtype: str
    """

    if not section_list:
        return default

    result = "another"
    if extra_char:
        result = f"{result}{extra_char}"
    return result

def print_error(msg: str) -> None:
    """common method for prompting errors so they stand out

    :param msg: error to display
    :type msg: str
    """
    print(f"{constants.ERROR_MARKER} {msg}")

def make_operation_id(uri: str, method: str) -> str:
    """The operation_id is a label for the endpoint.
        It's used in the SOAR connector similar to a function name

    :param uri: endpoint, ex: /threats
    :type uri: str
    :param method: https method, ex: get
    :type method: str
    :return: create operation id such as get_threats
    :rtype: str
    """
    # find the last uri component
    last_part = uri.replace("/", "_").replace("{", "").replace("}", "") # strip off any special characters
    last_part = last_part.split(".")[0] # strip off any file extensions

    return f"{method}{last_part.capitalize()}".lower()

def make_ref(section_path: Union[str, list], key: str) -> str:
    """create an internal document reference path, ex. #/components/schemas/get_computers

    :param section_path: list or string for path
    :type section_path: Union[str, list]
    :param key: key for final reference
    :type key: str
    :return: completed path
    :rtype: str
    """
    internal_path = ["#"]
    if isinstance(section_path, list):
        internal_path += section_path
    else:
        internal_path += [section_path]
    internal_path += [key]

    return "/".join(internal_path)

def navigate_dict(target_dict: dict, path: list) -> dict:
    """walk a dictionary looking for the path provided. If the path isn't found, None is returned

    :param target_dict: original dictionary to navigate
    :type target_dict: dict
    :param path: list of dicts to navigate
    :type path: list
    :return: found dictionary path or None if path doesn't exist
    :rtype: Union[dict, None]
    """
    navigated_dict = target_dict if target_dict else {}
    for item in path:
        if item in navigated_dict:
            navigated_dict = navigated_dict[item]
        else:
            return {}

    return navigated_dict

def pad_existing(listing: list, padding=2) -> list:
    return [f"{' '*padding}{k}" for k in listing]

def get_parameters(doc: dict, path: list, conditions: dict) -> list:
    """
    Retrieve parameters from a nested dictionary based on a given path and conditions.

    Args:
        doc (dict): The nested dictionary to search.
        path (list): A list of keys representing the path to the desired parameters.
        conditions (dict): A dictionary of conditions to filter the parameters.

    Returns:
        list: A list of parameter keys that match the given path and conditions.
    """
    result = []
    location = doc
    path_items = list(path)
    path_item = path_items.pop(0) if path_items else None
    while path_item:
        if path_item in location:
            location = location[path_item]
            path_item = path_items.pop(0) if path_items else None
        else:
            break

    if not path_items:
        for item_key, item in location.items():
            found = False
            for condition_key, condition_value in conditions.items():
                if condition_key in item and item[condition_key] == condition_value:
                    found = True

            if found:
                result.append(item_key)

    return result

def convert_value(type: str, value: str) -> Union[str, int, float, bool]:
    """ convert a string encoded value to the proper format """
    if value:
        if type == constants.VALUE_INTEGER:
            return int(value)
        if type == constants.VALUE_NUMBER:
            return round(float(value))
        if type == constants.VALUE_BOOLEAN:
            return value.lower() == "true"
        if type == constants.VALUE_ARRAY and value[0] == "[" and value[-1] == "]":
            return eval(value)

    return value

def separate_multiple(str_list: str, separator=",") -> list:
    """ separate items separated by a separator into a list """
    return [item.strip() for item in str_list.split(separator)]
