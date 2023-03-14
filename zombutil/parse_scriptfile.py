import json
import re
from typing import Dict
from collections import defaultdict


def _strip_comments(scriptfile: str) -> str:
    """Strip any /* comments */ from the input, and return it."""
    scriptfile = re.sub(
        r'/\*.+?\*/',
        '',
        scriptfile,
        flags=re.DOTALL
    )
    scriptfile = re.sub(
        r'-----+',
        '',
        scriptfile
    )
    return scriptfile


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
        r'module \w+',
        '',
        scriptfile
    )

    # Escape instances of `"`
    scriptfile = re.sub(
        r'"',
        '\\"',
        scriptfile
    )

    # Seems like `;` is the list separator character. Make lists on one line,
    # like in GunFighter_Reloading_Items.txt, and sort it out later.
    scriptfile = re.sub(
        r';\s*?\n',
        ';',
        scriptfile
    )

    # Turn `item foo { ... }` into `"item foo": { ... },`
    scriptfile = re.sub(
        r'\s*\b(.+?)\s*\n?\s*{',
        r'''"\1": {\n''',
        scriptfile
    )
    scriptfile = re.sub(
        r'}',
        '},',  # We'll have to get rid of the last comma in a list, later
        scriptfile
    )

    # Turn `fieldname = value,` or `fieldname:value,` into `"fieldname": "value",`
    scriptfile = re.sub(
        r'\s*\b(.+?)\s*[:=]\s*(.+?)\s*([,}])',
        r'"\1": "\2"\3',
        scriptfile
    )

    # Turn `Bolt_Bear_Pack,` into `Bolt_Bear_Pack: true`
    # Check Bolt_Bear.txt in Brita's Weapon Pack for this use case.
    scriptfile = re.sub(
        r'\n\s*([^:}]+?)\s*,',
        r'"\1": true,',
        scriptfile
    )

    # Have to get rid of the last comma in each list
    # Note: we still have to clean up the root element's trailing comma.
    scriptfile = re.sub(
        r',\s*}',
        '}',
        scriptfile
    )

    # Get rid of empty commas (why do these exist??)
    scriptfile = re.sub(
        r',\s*,',
        ',',
        scriptfile
    )

    scriptfile = scriptfile.strip()

    if len(scriptfile) <= 1:
        # This is an empty JSON string by now. Weird.
        scriptfile = '{}'

    if scriptfile[-1] == ',':
        # Get rid of the trailing comma after the root element
        scriptfile = scriptfile[:-1]

    return scriptfile


def _cleanup_json(json_obj: Dict) -> Dict[str, Dict[str, Dict]]:
    """
    Tidies up the resulting JSON a little, group stuff like Items together.
    """
    grouped_dict: Dict[str, Dict[str, Dict]] = defaultdict(dict)

    for key, pz_entity_data in json_obj.items():
        if key == 'imports':
            continue  # Don't care

        # In "fixing Fix 10855_Silver", the first word is the entity type and
        # the last is the specific name.
        pz_entity_type, *_, pz_entity_name = key.split(' ')

        if pz_entity_type in ['model', 'sound', ]:
            continue  # Don't care

        grouped_dict[pz_entity_type][pz_entity_name] = pz_entity_data

    return grouped_dict


def parse_scriptfile_contents_as_json(scriptfile: str) -> Dict[str, Dict[str, Dict]]:
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
                huge_json_object = {**huge_json_object, **file_as_json}
    """

    json_string = _pretend_its_json(_strip_comments(scriptfile))
    json_dict = {}

    # Might throw a json.decoder.JSONDecodeError
    json_dict = json.loads(json_string)

    tidied_json = _cleanup_json(json_dict)
    return tidied_json
