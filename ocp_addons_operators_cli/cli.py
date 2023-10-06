import datetime
import os
import sys
import time

import click
from pyaml_env import parse_config

from ocp_addons_operators_cli.click_dict_type import DictParamType
from ocp_addons_operators_cli.constants import INSTALL_STR, UNINSTALL_STR
from ocp_addons_operators_cli.utils.cli_utils import (
    get_addons_from_user_input,
    get_operators_from_user_input,
    prepare_addons,
    prepare_operators,
    run_install_or_uninstall_products,
    set_parallel,
    verify_user_input,
)


@click.command("installer")
@click.option(
    "-a",
    "--action",
    type=click.Choice([INSTALL_STR, UNINSTALL_STR]),
    help="Action to perform",
)
@click.option(
    "-o",
    "--operator",
    type=DictParamType(),
    help="""
\b
Operator to install.
Format to pass is:
    'name=operator1;namespace=operator1_namespace; channel=stable;target-namespaces=ns1,ns2;iib=/path/to/iib:123456'
Optional parameters:
    namespace - Operator namespace
    channel - Operator channel to install from, default: 'stable'
    source - Operator source, default: 'redhat-operators'
    target-namespaces - A list of target namespaces for the operator
    iib - To install an operator using custom iib
    """,
    multiple=True,
)
@click.option(
    "-a",
    "--addon",
    type=DictParamType(),
    help="""
\b
Addon to install.
Format to pass is:
    'name=addon1;param1=1;param2=2;rosa=true;timeout=60'
Optional parameters:
    addon parameters - needed parameters for addon installation.
    timeout - addon install / uninstall timeout in seconds, default: 30 minutes.
    rosa - if true, then it will be installed using ROSA cli.
    """,
    multiple=True,
)
@click.option(
    "-e",
    "--endpoint",
    help="SSO endpoint url",
    default="https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token",
    show_default=True,
)
@click.option(
    "-t",
    "--ocm-token",
    help="OCM token (Taken from oc environment OCM_TOKEN if not passed)",
    default=os.environ.get("OCM_TOKEN"),
)
@click.option(
    "--brew-token",
    help="""
    \b
    Brew token (needed to install managed-odh addon in stage).
    Default value is taken from environment variable, else will be taken from --brew-token flag.
    """,
    default=os.environ.get("BREW_TOKEN"),
)
@click.option("-c", "--cluster-name", help="Cluster name")
@click.option(
    "--kubeconfig",
    help="Path to kubeconfig file",
    type=click.Path(exists=True),
    show_default=True,
)
@click.option(
    "-p",
    "--parallel",
    help="Run install/uninstall in parallel",
    is_flag=True,
    show_default=True,
)
@click.option("--debug", help="Enable debug logs", is_flag=True)
def main(**kwargs):
    click.echo(f"Click Version: {click.__version__}")
    click.echo(f"Python Version: {sys.version}")

    # TODO: add params from yaml file
    user_kwargs = kwargs
    clusters_yaml_config_file = user_kwargs.get("clusters_yaml_config_file")
    if clusters_yaml_config_file:
        # Update CLI user input from YAML file if exists
        # Since CLI user input has some defaults, YAML file will override them
        user_kwargs.update(parse_config(path=clusters_yaml_config_file))

    action = user_kwargs.get("action")
    operators = get_operators_from_user_input(**user_kwargs)
    addons = get_addons_from_user_input(**user_kwargs)
    endpoint = user_kwargs.get("endpoint")
    brew_token = user_kwargs.get("brew_token")
    debug = user_kwargs.get("debug")
    ocm_token = user_kwargs.get("ocm_token")
    parallel = set_parallel(
        user_input_parallel=user_kwargs.get("parallel"),
        operators=operators,
        addons=addons,
    )
    user_kwargs["operators"] = operators
    user_kwargs["addons"] = addons
    install = action == INSTALL_STR
    user_kwargs["install"] = install

    verify_user_input(**user_kwargs)

    operators = prepare_operators(
        operators=operators, brew_token=brew_token, install=install
    )
    addons = prepare_addons(
        addons=addons,
        ocm_token=ocm_token,
        endpoint=endpoint,
        brew_token=brew_token,
        install=install,
    )

    run_install_or_uninstall_products(
        operators=operators,
        addons=addons,
        parallel=parallel,
        debug=debug,
        install=install,
    )


if __name__ == "__main__":
    start_time = time.time()
    try:
        main()
    finally:
        elapsed_time = datetime.timedelta(seconds=time.time() - start_time)
        click.secho(f"Total execution time: {elapsed_time}", fg="green", bold=True)
