import multiprocessing
import os

import click
from click_dict_type import DictParamType
from constants import TIMEOUT_30MIN
from ocm_python_client.exceptions import NotFoundException
from ocm_python_wrapper.cluster import ClusterAddOn
from ocm_python_wrapper.ocm_client import OCMPythonClient
from utils import set_debug_os_flags


def extract_addon_params(addon_dict):
    """
    Extract addon parameters from user input

    Args:
        addon_dict (dict): dict constructed from addon user input

    Returns:
        list: list of addon parameters dicts

    """
    exclude_list = ["cluster_addon", "name", "timeout", "rosa"]
    resource_parameters = []

    for key, value in addon_dict.items():
        if key in exclude_list:
            continue

        resource_parameters.append({"id": key, "value": value})

    return resource_parameters


def run_action(action, addons_tuple, parallel, brew_token=None, api_host="stage"):
    jobs = []
    for _addon in addons_tuple:
        cluster_addon_obj = _addon["cluster_addon"]
        addon_action_func = getattr(cluster_addon_obj, action)
        kwargs = {
            "wait": True,
            "wait_timeout": _addon.get("timeout", TIMEOUT_30MIN),
            "rosa": bool(_addon.get("rosa")),
        }
        if action == "install_addon":
            kwargs["parameters"] = _addon["parameters"]
            if cluster_addon_obj.addon_name == "managed-odh" and api_host == "stage":
                if brew_token:
                    kwargs["brew_token"] = brew_token
                else:
                    click.echo(
                        f"--brew-token flag for {cluster_addon_obj.addon_name} addon install is missing"
                    )
                    raise click.Abort()

        if parallel:
            job = multiprocessing.Process(
                name=f"{cluster_addon_obj.addon_name}---{action}",
                target=addon_action_func,
                kwargs=kwargs,
            )
            jobs.append(job)
            job.start()
        else:
            addon_action_func(**kwargs)

    failed_jobs = {}
    for _job in jobs:
        _job.join()
        if _job.exitcode != 0:
            failed_jobs[_job.name] = _job.exitcode

    if failed_jobs:
        click.echo(f"Some jobs failed to {action}: {failed_jobs}\n")
        raise click.Abort()


@click.group()
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
    required=True,
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
    "--token",
    help="OCM token (Taken from oc environment OCM_TOKEN if not passed)",
    required=True,
    default=os.environ.get("OCM_TOKEN"),
)
@click.option(
    "--brew-token",
    help="""
    \b
    Brew token (needed to install managed-odh addon in stage).
    Default value is taken from environment variable, else will be taken from --brew-token flag.
    """,
    required=False,
    default=os.environ.get("BREW_TOKEN"),
)
@click.option("-c", "--cluster", help="Cluster name", required=True)
@click.option("--debug", help="Enable debug logs", is_flag=True)
@click.option(
    "--api-host",
    help="API host",
    default="stage",
    type=click.Choice(["stage", "production"]),
    show_default=True,
)
@click.option(
    "-p",
    "--parallel",
    help="Run addons install/uninstall in parallel",
    is_flag=True,
    show_default=True,
)
@click.pass_context
def addons(
    ctx,
    addon,
    token,
    api_host,
    cluster,
    endpoint,
    debug,
    parallel,
    brew_token,
):
    """
    Command line to Install/Uninstall Addons on OCM managed cluster.
    """
    ctx.ensure_object(dict)
    ctx.obj["parallel"] = parallel
    ctx.obj["brew_token"] = brew_token
    ctx.obj["api_host"] = api_host

    if debug:
        set_debug_os_flags()

    _client = OCMPythonClient(
        token=token,
        endpoint=endpoint,
        api_host=api_host,
        discard_unknown_keys=True,
    ).client

    addon_tuple = addon
    for _addon in addon_tuple:
        try:
            _addon["cluster_addon"] = ClusterAddOn(
                client=_client, cluster_name=cluster, addon_name=_addon["name"]
            )
        except NotFoundException as exc:
            click.echo(f"{exc}")
            raise click.Abort()

        _addon["parameters"] = extract_addon_params(addon_dict=_addon)

    ctx.obj["addons_tuple"] = addon_tuple


@addons.command()
@click.pass_context
def install(ctx):
    """Install cluster Addons."""
    run_action(
        action="install_addon",
        addons_tuple=ctx.obj["addons_tuple"],
        parallel=ctx.obj["parallel"],
        brew_token=ctx.obj["brew_token"],
        api_host=ctx.obj["api_host"],
    )


@addons.command()
@click.pass_context
def uninstall(ctx):
    """Uninstall cluster Addons."""
    run_action(
        action="uninstall_addon",
        addons_tuple=ctx.obj["addons_tuple"],
        parallel=ctx.obj["parallel"],
    )
