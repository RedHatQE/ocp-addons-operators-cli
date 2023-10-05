import datetime
import os
import time

import click

from ocp_addons_operators_cli.click_dict_type import DictParamType
from ocp_addons_operators_cli.constants import INSTALL_STR, UNINSTALL_STR
from ocp_addons_operators_cli.utils.cli_utils import (
    get_addons_from_user_input,
    get_operators_from_user_input,
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
    user_kwargs = kwargs
    # TODO: add params from yaml file
    action = user_kwargs.get("action")
    operators = get_operators_from_user_input(**user_kwargs)
    addons = get_addons_from_user_input(**user_kwargs)
    user_kwargs.get("endpoint")
    user_kwargs.get("brew_token")
    user_kwargs.get("debug")
    user_kwargs.get("kubeconfig")
    user_kwargs.get("cluster_name")
    user_kwargs.get("ocm_token")
    user_kwargs.get("parallel")

    user_kwargs["operators"] = operators
    user_kwargs["addons"] = addons
    install = action == INSTALL_STR
    user_kwargs["install"] = install

    verify_user_input(**user_kwargs)


if __name__ == "__main__":
    start_time = time.time()
    try:
        main()
    finally:
        elapsed_time = datetime.timedelta(seconds=time.time() - start_time)
        click.secho(f"Total execution time: {elapsed_time}", fg="green", bold=True)
