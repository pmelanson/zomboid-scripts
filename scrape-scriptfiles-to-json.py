#!/bin/python3

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

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
    'CritDmgMultiplier', 'AimingPerkHitChanceModifier',
    'AimingPerkCritModifier', 'ProjectileCount', 'PiercingBullets',
    'MaxHitCount', 'JamGunChance', 'AimingTime', 'ReloadTime',
    'SoundVolume', 'SoundRadius',
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

DUMP_DIR = Path('csv-dump')


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
                # Group weapons by caliber.
                pz_item_type = pz_item_data['AmmoType'].replace('Base.', '') + ' gun'
            else:
                pz_item_type = 'Melee'

        elif pz_item_type == 'Container' and 'CanBeEquipped' in pz_item_data:
            # Split bags out.
            pz_item_type = 'Bag'

        elif pz_item_type == 'Clothing':
            # Split clothing out as well.
            pass

        else:
            # This is an item we don't care about. Skip!
            continue

        grouped_dict[pz_item_type][pz_item_name] = pz_item_data

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

            if 'gun' in pz_item_type:
                fieldnames = GUN_COLUMN_NAMES
            elif pz_item_type == 'Melee':
                fieldnames = MELEE_COLUMN_NAMES
            elif pz_item_type == 'Clothing':
                fieldnames = CLOTHING_COLUMN_NAMES
            elif pz_item_type == 'Bag':
                fieldnames = BAG_COLUMN_NAMES

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

            # We have a list of all .txt scriptfiles, scrape them now!
            for scriptfile in scriptfiles:
                for blacklist in [
                    'GunFighter_Sounds.txt',
                    '2022_02_16_List of Armor.txt',
                    'Beret.txt',
                    'Jur.txt',
                    'ammomaker_items.txt',
                    'ammomaker_recipes.txt',
                    'ambc_recipes.txt',
                    'tsarslib',
                ]:
                    if blacklist in scriptfile.parts:
                        # These files are hard and/or broken
                        continue

                with scriptfile.open() as scriptfile:
                    # Parse and append a single scriptfile
                    print(f'Parsing {scriptfile.name} to JSON!')
                    as_json = parse_scriptfile_contents_as_json(scriptfile.read())
                    for entity_type, entity_dict in as_json.items():
                        parsed_script_objects[entity_type] = {
                            **parsed_script_objects[entity_type], **entity_dict
                        }

    # Write various .csvs
    _dump_json_into_csvs(parsed_script_objects)

    # And also dump the json for fun
    with Path(DUMP_DIR / 'dump.json').open('w') as json_dump_file:
        json.dump(parsed_script_objects, json_dump_file, sort_keys=True, indent=4)


if __name__ == '__main__':
    main()
