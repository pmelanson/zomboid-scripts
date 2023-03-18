import re
from typing import Dict, List, Tuple

ITEM_OBJECT_AND_PAYLOAD_PATTERN = r'item ([\w ]+)[^{]*{([^}]+)}'  # Two matching groups
ITEM_ATTRIB_AND_VALUE_PATTERN = r'([\w]+)\s*=\s*([^,]+)'  # Two matching groups


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

    # Fuck tabstops
    #   - patrick 2020 and you can quote me on that
    scriptfile = re.sub(
        r'\t',
        ' ',
        scriptfile
    )

    return scriptfile


def _extract_items(scriptfile: str) -> List[Tuple[str, str]]:
    """From a file, extract a lot of
    "item ChestRig": "Weight=0.5,Type=Clothing"
    """

    return re.findall(ITEM_OBJECT_AND_PAYLOAD_PATTERN, scriptfile)


def _extract_item_attributes(item_payload: str) -> Dict[str, str]:
    """From an item's data, extract all the attributes into nice strings, e.g. 
    """

    results = re.findall(ITEM_ATTRIB_AND_VALUE_PATTERN, item_payload)
    return {match[0]: re.sub(r'\s+', ' ', match[1]).strip() for match in results}


def parse_scriptfile_contents_into_dict(scriptfile: str) -> Dict[str, Dict[str, str]]:
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

    output_json: Dict[str, Dict[str, str]] = {}

    items_and_payloads = _extract_items(_strip_comments(scriptfile))
    for item, payload in items_and_payloads:
        output_json[item.strip()] = _extract_item_attributes(payload)

    return output_json
