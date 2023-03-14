#!/bin/python3

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple

from zombutil.parse_scriptfile import parse_scriptfile_contents_as_json

parser = argparse.ArgumentParser(
    description='''Given scriptfiles, parse them as JSON objects
Example:
python3 scrape-scriptfiles-to-json.py -d "/mnt/c/Program Files (x86)/Steam/steamapps/workshop"
'''
)

parser.add_argument(
    '-f', '--scriptfile',
    help='A single scriptfile to parse'
)
parser.add_argument(
    '-d', '--workshop_dir',
    help='Path to the workshop directory of zomboid mods'
)

GUN_COLUMN_NAMES = [
    'DisplayName', 'AttachmentType', 'AmmoType', 'MagazineType', 'MaxAmmo',
    'MinDamage', 'MaxDamage', 'HitChance', 'CriticalChance',
    'CritDmgMultiplier', 'ProjectileCount', 'PiercingBullets',
    'MaxHitCount', 'JamGunChance', 'AimingTime', 'ReloadTime',
    'SoundRadius', 'MinRange', 'MaxRange', 'Weight',
    'AimingPerkHitChanceModifier', 'AimingPerkCritModifier', 'ConditionMax',
    'ConditionLowerChanceOneIn', 'PushBackMod', 'KnockdownMod', 'BaseID',
    'AttachmentsList',
]

MELEE_COLUMN_NAMES = [
    'DisplayName', 'Categories', 'MaxDamage', 'MinDamage', 'MinRange',
    'MaxRange', 'CriticalChance', 'MinimumSwingTime', 'SwingAnim',
    'KnockdownMod', 'Tags',
]

CLOTHING_COLUMN_NAMES = [
    'DisplayName', 'BodyLocation', 'BiteDefense',
    'RunSpeedModifier', 'CombatSpeedModifier', 'Insulation',
    'NeckProtectionModifier', 'Weight',
]

BAG_COLUMN_NAMES = [
    'DisplayName', 'CanBeEquipped', 'Capacity', 'WeightReduction',
    'RunSpeedModifier', 'clothingExtraSubmenu', 'BodyLocation',
    'Weight',
]

ATTACHMENT_COLUMN_NAMES = [
    'BaseID', 'DisplayName', 'PartType', 'WeightModifier',
    'HitChanceModifier', 'MinRangeModifier', 'MaxRangeModifier',
    'AimingTimeModifier', 'RecoilDelayModifier', 'ReloadTimeModifier',
    'AngleModifier', 'MountOn',  # MountOn as the last field, since it's usually so massive.
]

DUMP_DIR = Path('output')


def _group_into_spreadsheets(json_data: Dict[str, Dict[str, Dict]]) -> Dict[str, Dict[str, Dict]]:
    """
    Do stuff like split weapons into 5.56, .44, .45 ACP, 9mm etc.
    Filter only stuff we care about.
    """

    grouped_dict: Dict[str, Dict[str, Dict]] = defaultdict(dict)
    item_dict = json_data['item']

    for pz_item_name, pz_item_data in item_dict.items():
        # "10gShotgunShells": {"Count": 5, [..]}

        try:
            pz_item_type = pz_item_data['Type']
        except KeyError:
            print(f'{pz_item_name} has no Type, skipping')
            continue

        if pz_item_type == 'Weapon':
            if 'AmmoType' in pz_item_data:
                pz_item_type = 'Gun'
            else:
                pz_item_type = 'Melee'

        elif pz_item_type == 'Container' and 'CanBeEquipped' in pz_item_data:
            # Split bags out.
            pz_item_type = 'Bag'

        elif pz_item_type == 'Clothing':
            # Split clothing out as well.
            pass

        elif pz_item_type == 'WeaponPart':
            # Split out attachments.
            pz_item_type = 'Attachment'

        else:
            # This is an item we don't care about. Skip!
            continue

        # Put the BaseID in the dict as well, if we need it.
        pz_item_data['BaseID'] = pz_item_name
        grouped_dict[pz_item_type][pz_item_name] = pz_item_data

    # Post-processing; add a gun -> attachments mapping
    gun_to_attachment_map: Dict[str, List[str]] = defaultdict(list)
    for attachment_name, attachment_data in grouped_dict['Attachment'].items():
        mountable_weapons_list = attachment_data['MountOn'].split(';')
        mountable_weapons_list = [item.strip() for item in mountable_weapons_list]
        for weapon_id in mountable_weapons_list:
            gun_to_attachment_map[weapon_id].append(attachment_name)

    for gun, attachment_list in gun_to_attachment_map.items():
        try:
            grouped_dict['Gun'][gun]['AttachmentsList'] = ';'.join(attachment_list)
        except KeyError:
            pass

    return grouped_dict


def _dump_json_into_csvs(json_data: Dict[str, Dict[str, Dict]]):
    """
    Given a JSON dump, split it out into some .csvs in the csv-dump/ subdir.
    """
    grouped_data = _group_into_spreadsheets(json_data)

    DUMP_DIR.mkdir(exist_ok=True)

    for pz_item_type, pz_items_dict in grouped_data.items():
        with Path(DUMP_DIR / f'{pz_item_type}.csv').open('w') as csv_file:
            print(f'Writing {csv_file.name}!')
            fieldnames: List[str]

            if 'Gun' in pz_item_type:
                fieldnames = GUN_COLUMN_NAMES
            elif pz_item_type == 'Melee':
                fieldnames = MELEE_COLUMN_NAMES
            elif pz_item_type == 'Clothing':
                fieldnames = CLOTHING_COLUMN_NAMES
            elif pz_item_type == 'Bag':
                fieldnames = BAG_COLUMN_NAMES
            elif pz_item_type == 'Attachment':
                fieldnames = ATTACHMENT_COLUMN_NAMES

            writer = csv.DictWriter(
                csv_file, fieldnames=fieldnames, extrasaction='ignore'
            )
            writer.writeheader()

            for pz_item in pz_items_dict.values():
                writer.writerow(pz_item)


def _get_scripts_from_moddir(mod_dir: Path) -> List[Path]:
    """Finds all scriptfiles in moddir/media/scripts."""
    scriptfiles: List[Path] = []
    scripts_dir = mod_dir / 'media' / 'scripts'

    if scripts_dir.exists() and scripts_dir.is_dir():
        print(f'Found scripts folder in {mod_dir.name}!')

        files_to_search: List[Path] = []

        for file_or_dir in scripts_dir.iterdir():
            if file_or_dir.is_dir():
                for file in file_or_dir.iterdir():
                    files_to_search.append(file)
            if file_or_dir.is_file():
                files_to_search.append(file_or_dir)

        for file in files_to_search:
            if file.suffix.lower() == '.txt':
                scriptfiles.append(file)

    return scriptfiles


def main():
    args = parser.parse_args()

    parsed_script_objects: Dict[str, Dict[str, Dict]] = defaultdict(dict)

    if args.scriptfile:
        with Path(args.scriptfile).open() as scriptfile:
            # Parse and append a single scriptfile
            parsed_script_objects = parse_scriptfile_contents_as_json(scriptfile.read())
    if args.workshop_dir:
        with Path(args.workshop_dir) as top_level_dir:

            # Navigate down until we are in the zomboid mod directory
            if top_level_dir.name == 'workshop':
                top_level_dir /= 'content'
            if top_level_dir.name == 'content':
                top_level_dir /= '108600'

            assert top_level_dir.is_dir()

            # Find all instances of mod_dir/mods/modname/media/scripts/*/script.txt
            scriptfiles: List[Path] = []
            for workshop_dir in top_level_dir.iterdir():
                workshop_dir /= 'mods'

                for mod_dir in workshop_dir.iterdir():
                    scriptfiles.extend(_get_scripts_from_moddir(mod_dir))

            faulty_scriptfiles: List[Tuple[Path, Exception]] = []

            # We have a list of all .txt scriptfiles, scrape them now!
            for scriptfile in scriptfiles:
                is_blacklisted_scriptfile = False
                for blacklist in [
                    'GunFighter_Sounds.txt',
                    '2022_02_16_List of Armor.txt',
                    'ammomaker_items.txt',
                    'ammomaker_recipes.txt',
                    'ambc_recipes.txt',
                    'vehicles'
                ]:
                    if blacklist in scriptfile.parts:
                        # These files are hard and/or broken
                        is_blacklisted_scriptfile = True
                if is_blacklisted_scriptfile:
                    continue

                # Parse and append a single scriptfile
                print(f'Parsing {scriptfile.name} to JSON!')

                scriptfile_contents = ''
                successfully_read_scriptfile = False
                for encoding in ['utf-8', 'windows-1252', 'windows-1250']:
                    try:
                        with scriptfile.open(encoding=encoding) as fd:
                            scriptfile_contents = fd.read()
                        successfully_read_scriptfile = True
                    except UnicodeDecodeError:
                        print(f'Failed to read {scriptfile.name} with {encoding} encoding. Trying another encoding.')
                    else:
                        break  # Found a correct encoding
                if not successfully_read_scriptfile:
                    # Can't read this file, get an example exception and give up.
                    try:
                        with scriptfile.open() as bad_scriptfile_fd:
                            bad_scriptfile_fd.read()
                    except UnicodeDecodeError as e:
                        faulty_scriptfiles.append((scriptfile.name, e))
                    continue  # Welp, time to give up and go to the next file

                try:
                    as_json = parse_scriptfile_contents_as_json(scriptfile_contents)
                except json.decoder.JSONDecodeError as e:
                    print(f'Huh, my file parsing choked a bit there: {e}')
                    faulty_scriptfiles.append((scriptfile.name, e))
                    continue

                for entity_type, entity_dict in as_json.items():
                    parsed_script_objects[entity_type] = {
                        **parsed_script_objects[entity_type], **entity_dict
                    }

    # Write various .csvs
    _dump_json_into_csvs(parsed_script_objects)

    # And also dump the json for fun
    with Path(DUMP_DIR / 'dump.json').open('w') as json_dump_file:
        json.dump(parsed_script_objects, json_dump_file, sort_keys=True, indent=4)

    print('\n')
    print('Faulty scriptfiles:')
    for scriptfile_name, scriptfile_exception in faulty_scriptfiles:
        print(scriptfile_exception, scriptfile_name, file=sys.stderr)
        if isinstance(scriptfile_exception, json.decoder.JSONDecodeError):
            # Bit of extra json help
            e_index = scriptfile_exception.pos
            debug_text = (scriptfile_exception.doc[e_index - 40:e_index - 1]
                          + '→' + scriptfile_exception.doc[e_index] + '←'
                          + scriptfile_exception.doc[e_index + 1:e_index + 40])
            print(debug_text.replace('\n', '\\n'))


if __name__ == '__main__':
    main()
