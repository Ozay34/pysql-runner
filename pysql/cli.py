import argparse
import sys

from pysql.parser.parse import parser as lang
from .preset import *

def main():

    # Handle preset subcommand separately because subparsers don't support generic/wildcard names
    if len(sys.argv) > 1 and sys.argv[1].lower() == "preset":
        preset()
        return

    parser = argparse.ArgumentParser(
        prog="pysql",
        description="run sql files with embedded python",
        usage="pysql <file> [options]"
    )

    parser.add_argument("file", type=argparse.FileType("r"), help="name of the file to execute")
    parser.add_argument("preset", action="store_false", help="use 'pysql preset -h' for more information")
    parser.add_argument("-v", "--verbose", action="store_true", help="enable verbose logging")
    parser.add_argument("-c", "--connection", action="extend", nargs="+", help="set default connection(s)")

    args = parser.parse_args()

    lang.parse(args.file.read())


def preset():
    parser = argparse.ArgumentParser(
        prog="pysql preset",
        description="view and modify saved connections for your current user",
        usage="pysql preset <command> [options]"
    )
    parser.add_argument("preset", help=argparse.SUPPRESS)
    subparser = parser.add_subparsers(required=True)

    # List command
    list_parser = subparser.add_parser("list", aliases=["l"], help="list saved connections", usage="pysql preset list [name] [options]")
    list_parser.set_defaults(func=preset_list)
    list_parser.add_argument("name", nargs="?", help="optional name of a specific preset to show")
    list_parser.add_argument("-u", "--unsafe", action="store_true", help="display passwords in plain text")

    # Add command
    add_parser = subparser.add_parser("add", aliases=["a"], help="add a connection", usage="pysql preset add <name> [options]")
    add_parser.set_defaults(func=preset_add)
    add_parser.add_argument("name", help="unique name to use for this connection")

    add_one_group = add_parser.add_argument_group("connections", "args to add a single connection, cannot be used with group args")
    add_one_group.add_argument("-d", "--driver", help="internal driver that will be used to execute statements")
    add_one_group.add_argument("-c", "--connection", help="connection string passed to the driver specified")
    add_one_group.add_argument("-u", "--username", help="username for the connection")
    add_one_group.add_argument("-p", "--password", help="password for the connection")

    add_many_group = add_parser.add_argument_group("group", "args to add a connection group, cannot be used with connection args")
    add_many_group.add_argument("-g", "--group", action="extend", nargs="+", help="list other connections to create a group")

    # Remove command
    remove_parser = subparser.add_parser("remove", aliases=["r"], help="remove a connection", usage="pysql preset remove <name> [options]")
    remove_parser.set_defaults(func=preset_remove)
    remove_parser.add_argument("name", help="name of the connection to remove")
    remove_parser.add_argument("-f", "--force", action="store_true", help="flag to skip confirmation input")

    # Update command
    update_parser = subparser.add_parser("update", aliases=["u"], help="update a connection", usage="pysql preset update <name> [options]")
    update_parser.set_defaults(func=preset_update)
    update_parser.add_argument("name", help="name of an existing connection or group to update")

    update_one_group = update_parser.add_argument_group("connections", "args to update a single connection, cannot be used with group args")
    update_one_group.add_argument("-d", "--driver", help="internal driver that will be used to execute statements")
    update_one_group.add_argument("-c", "--connection", help="connection string passed to the driver specified")
    update_one_group.add_argument("-u", "--username", help="username for the connection")
    update_one_group.add_argument("-p", "--password", help="password for the connection")

    update_many_group = update_parser.add_argument_group("groups", "args to update connection groups, cannot be used with connection args")
    update_many_group.add_argument("-a", "--append", action="extend", nargs="+", help="add the given connections to this group")
    update_many_group.add_argument("-r", "--remove", action="extend", nargs="+", help="remove the given connections from this group")

    # Import command
    import_parser = subparser.add_parser("import", aliases=["i"], help="import a set of connections", usage="pysql preset import <file>")
    import_parser.set_defaults(func=preset_import)
    import_parser.add_argument("file", type=argparse.FileType("r"), help="json file to import connection information from")
    import_parser.add_argument("-t", "--type", choices=["json", "csv"], help="force the file import type instead of infering file extension")
    import_parser.add_argument("-d", "--delim", default=",", help="specify the delimiter used in csv files")

    args = parser.parse_args()
    args.func(**vars(args))
