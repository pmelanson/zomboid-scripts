import re
from typing import Dict, List, Optional, Tuple

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


def _categorize_gun(item_payload: Dict[str, str]) -> Optional[str]:
    """
    Given a gun's data, put a label like "Shotgun" on it.
    """
    try:
        if 'ShotgunShell' in item_payload['AmmoType']:
            # It's a shotgun
            return 'Shotgun'
        if item_payload['AttachmentType'] == 'Holster':
            # Call it a handgun why not
            return 'Handgun'
        elif item_payload['AttachmentType'] == 'Rifle':
            return 'Rifle'
        else:
            return 'Other'
    except:
        if 'IsAimedFirearm' in item_payload:
            # It's still some sort of gun, return Other (this deals with stuff like the Sling Shot)
            return 'Other'
        else:
            return None


def _categorize_weapon(item_payload: Dict[str, str]) -> Optional[str]:
    try:
        if 'Melee' in item_payload['DisplayName']:
            # Don't care how many guns you can swing like a bat
            return 'MeleeGun'
        elif 'IsAimedFirearm' in item_payload:
            # This is a gun, and you're not swinging it like a bat
            return 'Gun'
        else:
            # This is a non-gun weapon, i.e. a melee weapon
            return 'Melee'
    except KeyError:
        return None


def _cleanup_attributes(item_payload: Dict[str, str]) -> Dict[str, str]:
    """Do some final data cleanup."""
    try:
        item_payload['AmmoType'] = item_payload['AmmoType'].replace('Base.', '')
    except KeyError:
        pass

    try:
        item_payload['MagazineType'] = item_payload['MagazineType'].replace('Base.', '')
    except KeyError:
        pass

    if 'MaxDamage' in item_payload and 'MinDamage' not in item_payload:
        # Make sure that MinDamage is always set.
        item_payload['MinDamage'] = 0

    if 'MaxRange' in item_payload and 'MinRange' not in item_payload:
        # Make sure that MinDamage is always set.
        item_payload['MinRange'] = 0

    return item_payload


def parse_scriptfile_contents_into_dict(scriptfile: str, mod_name: str) -> Dict[str, Dict[str, str]]:
    """
    Takes a string of the entire contents of a scriptfile, and massages it into
    a JSON format before parsing it and returning it as a dict.

    Example usage:
        with open("RUGER.txt") as file:
            ruger_objects = parse_scriptfile_contents_into_dict(file.read())

    Another example usage:
        huge_json_object = {}
        for filename in huge_list_of_filenames:
            with open(filename) as file:
                # Read and concatenate this scriptfile as a json object.
                file_as_json = parse_scriptfile_contents_into_dict(file.read())
                huge_json_object = {**huge_json_object, **file_as_json}
    """

    output_dict: Dict[str, Dict[str, str]] = {}

    items_and_payloads = _extract_items(_strip_comments(scriptfile))

    for item, payload in items_and_payloads:
        item_name = item.strip()
        item_payload = _cleanup_attributes(_extract_item_attributes(payload))
        if _categorize_weapon(item_payload):
            item_payload['WeaponType'] = _categorize_weapon(item_payload)
        if _categorize_gun(item_payload):
            item_payload['GunType'] = _categorize_gun(item_payload)
        item_payload['FromMod'] = mod_name
        
        output_dict[item_name] = item_payload

    return output_dict
