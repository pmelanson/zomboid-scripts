#!/bin/python3

import argparse
import json
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

    parsed_script_objects: Dict = {}

    if args.scriptfile:
        with Path(args.scriptfile).open() as scriptfile:
            # Parse and append a single scriptfile
            as_json = parse_scriptfile_contents_as_json(scriptfile.read())
            parsed_script_objects = {**parsed_script_objects, **as_json}
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
                with scriptfile.open() as scriptfile:
                    # Parse and append a single scriptfile
                    as_json = parse_scriptfile_contents_as_json(scriptfile.read())
                    parsed_script_objects = {**parsed_script_objects, **as_json}

    # Just dump all the JSON for now.
    print(json.dumps(parsed_script_objects, sort_keys=True, indent=4))


if __name__ == '__main__':
    main()
