import os
import json
import csv
import keyring
from pathlib import Path
from tabulate import tabulate
from importlib_metadata import entry_points

PRESET_FILE = os.environ.get("PYSQL_PRESET") or Path.joinpath(Path.home(), "pysql_presets.json")
DRIVERS = {driver.name: driver for driver in entry_points(group="pysql.drivers")}


def get_presets():
    try:
        with open(PRESET_FILE) as preset_file:
            presets = json.load(preset_file)
            for preset, config in presets.items():
                if "username" in config:
                    config["password"] = keyring.get_password(f"pysql.{preset}", presets[preset]["username"])
            return presets
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"error: presets file is not valid json: {PRESET_FILE}")
        exit(1)


def save_presets(presets):
    # Secure any passwords
    for preset, config in presets.items():
        if isinstance(config, dict) and "password" in config:
            keyring.set_password(f"pysql.{preset}", config["username"], config["password"])
            del config["password"]

    with open(PRESET_FILE, "w") as preset_file:
        json.dump(presets, preset_file, indent=4)


def print_presets(presets, unsafe=False):
    preset_table = [[
        preset,
        config["driver"],
        config["connection"],
        config["username"],
        config["password"] if unsafe else "******"
    ] for preset, config in presets.items() if isinstance(config, dict)]
    preset_group_table = [[
        preset, ",".join(group)
    ] for preset, group in presets.items() if isinstance(group, list)]

    if len(preset_table) > 0:
        if len(preset_group_table) > 0:
            print("\npreset connections:\n")
        print(tabulate(preset_table, headers=["preset", "driver", "connection", "username", "password"]))
    if len(preset_group_table) > 0:
        if len(preset_table) > 0:
            print("\npreset groups:\n")
        print(tabulate(preset_group_table, headers=["preset", "group"]))


def preset_list(name, unsafe, **kwargs):
    presets = get_presets()

    if name is not None:
        config = presets.get(name)
        if config is None:
            print(f"no preset with name '{name}'")
            return

        print_presets({name: config}, unsafe)
    else:
        if len(presets) == 0:
            print(f"no saved presets")
        print_presets(presets, unsafe)


def preset_add(name, driver, connection, username, password, group, **kwargs):
    single_add = any(x is not None for x in [driver, connection, username, password])
    group_add = any(x is not None for x in [group])
    if not single_add and not group_add:
        print("error: cannot create connection or group, no arguments specified")
        return
    if single_add and group_add:
        print("error: cannot combine connection and group update arguments")
        return

    presets = get_presets()
    if name in presets:
        print(f"error: preset '{name}' already exists")
        return

    if single_add:

        if driver is None:
            print(f"error: driver not specified, choose one of the installed drivers: {','.join(DRIVERS)}")
            return
        if connection is None:
            print("error: no connection string specified")
            return
        if username is None:
            print("warning: no username specified for the connection")
        if password is None:
            print("warning: no password specified for the connection")

        if driver not in DRIVERS:
            print(f"warning: driver not installed: {driver}")

        presets[name] = {
            "driver": driver,
            "connection": connection,
            "username": username,
            "password": password
        }

    if group_add:
        unrecognized = [preset for preset in group if preset not in presets]
        if len(unrecognized) > 0:
            print(f"warning: values in group are not presets: {','.join(unrecognized)}")

        presets[name] = group

    save_presets(presets)
    print(f"\nadded preset: {name}")


def preset_remove(name, force, **kwargs):
    presets = get_presets()
    if name not in presets:
        print(f"error: preset '{name}' does not exist")
        return

    print_presets({name: presets[name]})

    if not force:
        confirm = input("Remove preset? (Y/n):")
        if confirm.lower() == "n":
            return

    del presets[name]
    save_presets(presets)
    print(f"\nremoved preset: {name}")


def preset_update(name, driver, connection, username, password, append, remove, **kwargs):
    single_update = any(x is not None for x in [driver, connection, username, password])
    group_update = any(x is not None for x in [append, remove])
    if not single_update and not group_update:
        print("warning: no updates specified")
        return

    presets = get_presets()
    if name not in presets:
        print(f"error: preset '{name}' does not exist")
        return

    preset = presets[name]
    if single_update and not isinstance(preset, dict):
        print("error: attempting to update connection group as a single connection")
        return
    if group_update and not isinstance(preset, list):
        print("error: attempting to update single connection as a group")
        return

    if driver is not None:
        preset["driver"] = driver
    if connection is not None:
        preset["connection"] = connection
    if username is not None:
        preset["username"] = username
    if password is not None:
        preset["password"] = password

    if append is not None:
        preset += append
    if remove is not None:
        presets[name] = [name for name in preset if name not in remove]

    save_presets(presets)
    print(f"\nupdated preset: {name}")


def preset_import(file, type, delim, **kwargs):

    file_type = type or os.path.splitext(file.name)[1][1:]

    contents = {}
    if file_type == "json":
        try:
            contents = json.load(file)
        except json.JSONDecodeError:
            print(f"error: invalid json in file: {file.name}")

    if file_type == "csv":
        for i, line in enumerate(csv.reader(file, delimiter=delim)):
            if len(line) == 2:
                contents[line[0]] = line[1].split(",")
            elif len(line) == 5:
                contents[line[0]] = {
                    "driver": line[1],
                    "connection": line[2],
                    "username": line[3],
                    "password": line[4]
                }
            else:
                print(f"warning: skipping import of line {i+1} because it has the wrong number of columns")

    # Update presets
    presets = get_presets()
    presets.update(contents)
    save_presets(presets)
    print(f"finished importing file: {file.name}")
