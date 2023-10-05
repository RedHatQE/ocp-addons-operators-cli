import multiprocessing

import click
from ocm_python_client.exceptions import NotFoundException
from ocm_python_wrapper.cluster import ClusterAddOn
from ocm_python_wrapper.ocm_client import OCMPythonClient

from ocp_addons_operators_cli.constants import TIMEOUT_30MIN
from ocp_addons_operators_cli.utils import set_debug_os_flags


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
                        f"--brew-token flag for {cluster_addon_obj.addon_name} addon"
                        " install is missing"
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


def install(ctx):
    """Install cluster Addons."""
    run_action(
        action="install_addon",
        addons_tuple=ctx.obj["addons_tuple"],
        parallel=ctx.obj["parallel"],
        brew_token=ctx.obj["brew_token"],
        api_host=ctx.obj["api_host"],
    )


def uninstall(ctx):
    """Uninstall cluster Addons."""
    run_action(
        action="uninstall_addon",
        addons_tuple=ctx.obj["addons_tuple"],
        parallel=ctx.obj["parallel"],
    )
