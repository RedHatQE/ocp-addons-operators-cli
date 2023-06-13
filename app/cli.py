import sys

import click
from addon_cmds import commands as addons
from operator_cmds import commands as operators


@click.group()
def entry_point():
    """
    CLI to Install/Uninstall Addon/Operator on OCM/OCP

    \b
    Help on sub command:
        addon install --help
        addon uninstall --help
        operator install --help
        operator uninstall --help
    """
    # Entrypoint for all click groups (Addons and Operators)


def main():
    entry_point.add_command(addons.addons)
    entry_point.add_command(operators.operators)
    click.echo(f"Click Version: {click.__version__}")
    click.echo(f"Python Version: {sys.version}")
    _commands = {
        "addons": {
            "install": addons.install,
            "uninstall": addons.uninstall,
        },
        "operators": {
            "install": operators.install,
            "uninstall": operators.uninstall,
        },
    }
    user_args = sys.argv
    # In case called with multiple arguments and --help is specified
    # We want to show the sub command help
    if len(user_args) > 1:
        help_switch = "--help"
        _type = user_args[1]

        # In case called with --help only (No sub command, show default help)
        if _type == help_switch:
            entry_point(obj={})
        else:
            _type_commands = _commands.get(_type)
            if not _type_commands:
                click.echo(f"Available commands are: {'/'.join(_commands.keys())}\n")
                raise click.Abort()

            user_help_command = [arg.strip() for arg in user_args[-2:]]
            sub_command = _type_commands.get(user_help_command[0])
            if user_help_command[-1] == help_switch and sub_command:
                with click.Context(sub_command) as ctx:
                    click.echo(sub_command.get_help(ctx))
            else:
                entry_point(obj={})

    else:
        # In case called without arguments, show default help
        entry_point(obj={})


if __name__ == "__main__":
    main()
