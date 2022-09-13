import os
import csv
import re

item_block_begin_pattern = re.compile(r"\sitem\s(\S+)")
item_block_end_pattern = re.compile(r"}")
weapon_info_line = re.compile(r"=\s+(.+?)\s*,")
fieldnames = [
    'DisplayName',
    'Weight',
    'AttachmentType',
    'MaxAmmo',
    'AmmoType',
    'MagazineType',
    'MaxDamage',
    'MinDamage',
    'MinRange',
    'MaxRange',
    'HitChance',
    'SoundVolume',
    'SoundRadius',
    'PushBackMod',
    'KnockdownMod',
    'BaseID'
]

scripts_dir = input('Enter full path to directory of zomboid weapon.txt scripts: ')
csvfile_path = scripts_dir + '/../infodump.csv'


with open(csvfile_path, 'w', newline='') as csvfile:
    infodump_writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=',')
    infodump_writer.writeheader()

    current_weapon_data = {fieldname: '' for fieldname in fieldnames}
    print(f'Writing csv to {csvfile_path}')

    building_weapon_definition = False

    def flush_current_weapon():
        global building_weapon_definition
        global current_weapon_data
        assert building_weapon_definition
        infodump_writer.writerow(current_weapon_data)
        if '' in current_weapon_data.values():
            print(f"Had to shortcut for {current_weapon_data['BaseID']}")
        current_weapon_data = {fieldname: '' for fieldname in fieldnames}
        building_weapon_definition = False

    for weapon_data_filepath in os.listdir(scripts_dir):
        print(f"Reading {weapon_data_filepath}")
        with open(scripts_dir + "/" + weapon_data_filepath, 'r') as weapon_data_file:

            for line_n, line in enumerate(weapon_data_file):
                if item_block_begin_pattern.match(line):
                    # Begin looking for weapon data lines
                    if building_weapon_definition:
                        flush_current_weapon()
                    building_weapon_definition = True
                    current_weapon_data['BaseID'] = item_block_begin_pattern.match(line).groups()[0]
                    print(f"Reading block for {current_weapon_data['BaseID']}")
                elif building_weapon_definition and ('' not in current_weapon_data.values()):
                    # Write out all weapon data to a row in the output csv
                    flush_current_weapon()
                elif building_weapon_definition:
                    if re.search('SubCategory', line) and not re.search('Firearm', line):
                        print(f"Line {line_n}:")
                        print(f"Hold up, {current_weapon_data['BaseID']} isn't a gun!")
                        building_weapon_definition = False
                        current_weapon_data = {fieldname: '' for fieldname in fieldnames}
                        continue

                    for fieldname in fieldnames:
                        if re.search(f"\\b({fieldname})\\b", line):
                            #print(f"Found {fieldname} data")
                            field_value = weapon_info_line.search(line).groups()[0]
                            if current_weapon_data[fieldname] != '':
                                print(f"Line {line_n}:")
                                print(f"Warning! Overwriting {fieldname}, from {current_weapon_data[fieldname]} to {field_value}!")
                            current_weapon_data[fieldname] = field_value
                            break