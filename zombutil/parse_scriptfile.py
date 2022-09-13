import json
import re
from typing import Dict


def _strip_comments(scriptfile: str) -> str:
    """Strip any /* comments */ from the input, and return it."""
    return re.sub(
        r'/\*.+\*/',
        '',
        scriptfile
    )


def _pretend_its_json(scriptfile: str) -> str:
    """Modify the script file to make it look like JSON."""

    # Fuck tabstops
    #   - patrick 2020 and you can quote me on that
    scriptfile = re.sub(
        r'\t',
        ' ',
        scriptfile
    )

    # We use `module Base` as the root object
    scriptfile = re.sub(
        r'module Base',
        '',
        scriptfile
    )

    # Turn `item foo { ... }` into `"item foo": { ... },`
    scriptfile = re.sub(
        r'\s*\b(.+?)\s*\n?\s*{',
        r'''"\1": {''',
        scriptfile
    )
    scriptfile = re.sub(
        r'}',
        '},',  # We'll have to get rid of the last comma in a list, later
        scriptfile
    )

    # Turn `fieldname = value,` into `"fieldname": "value",`
    scriptfile = re.sub(
        r'(\w+)\s*[:=]\s*(.+?)\s*,',
        r'"\1": "\2",',
        scriptfile
    )

    # Have to get rid of the last comma in each list
    # Note: we still have to clean up the root element's trailing comma.
    scriptfile = re.sub(
        r',\s*}',
        '}',
        scriptfile
    )

    scriptfile = scriptfile.strip()

    if scriptfile[-1] == ',':
        # Get rid of the trailing comma after the root element
        scriptfile = scriptfile[:-1]

    return scriptfile


def parse_scriptfile_contents_as_json(scriptfile: str) -> Dict:
    """
    Takes a string of the entire contents of a scriptfile, and massages it into
    a JSON format before parsing it and returning it as a dict.

    Example usage:
        with open("RUGER.txt") as file:
            ruger_objects = parse_scriptfile_contents_as_json(file.read())

    Another example usage:
        huge_json_object = {}
        for filename in huge_list_of_filenames:
            with open(filename) as file:
                # Read and concatenate this scriptfile as a json object.
                file_as_json = parse_scriptfile_contents_as_json(file.read())
                huge_json_object = {
                    key: value for (key, value) in
                    (huge_json_object.items() + file_as_json.items())
                }
    """

    json_string = _pretend_its_json(_strip_comments(scriptfile))
    json_dict = json.loads(json_string)
    return json_dict
