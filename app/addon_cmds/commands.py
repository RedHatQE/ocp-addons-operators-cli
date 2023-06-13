import multiprocessing
import os

import click
from constants import TIMEOUT_30MIN
from ocm_python_wrapper.cluster import ClusterAddOn
from ocm_python_wrapper.ocm_client import OCMPythonClient
from utils import extract_operator_addon_params


def run_action(
    action, addons, parallel, timeout, rosa, brew_token=None, api_host="stage"
):
    jobs = []
    for values in addons.values():
        cluster_addon_obj = values["cluster_addon"]
        addon_action_func = getattr(cluster_addon_obj, action)
        kwargs = {
            "wait": True,
            "wait_timeout": timeout,
            "rosa": cluster_addon_obj.addon_name in rosa,
        }
        if action == "install_addon":
            kwargs["parameters"] = values["parameters"]
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
    "--addons",
    help="""
    \b
    Addons to install.
    Format to pass is 'addon_name_1|param1=1,param2=2'
    """,
    required=True,
    multiple=True,
)
@click.option(
    "--timeout",
    help="Timeout in seconds to wait for addon to be installed/uninstalled",
    default=TIMEOUT_30MIN,
    show_default=True,
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
@click.option(
    "--rosa",
    help="""
    \b
    Install/uninstall addons via ROSA cli.
    Specify addons with addon names, separated by a comma.
    Example:
    '-a addon_1 -a addon_2 -a addon_3 --rosa addon_name_2,addon_name_3';
    addon_2 and addon_3 will be installed with ROSA.
    """,
)
@click.pass_context
def addon(
    ctx,
    addons,
    token,
    api_host,
    cluster,
    endpoint,
    timeout,
    debug,
    parallel,
    brew_token,
    rosa,
):
    """
    Command line to Install/Uninstall Addons on OCM managed cluster.
    """
    _rosa = [addon_name.strip() for addon_name in rosa.split(",")] if rosa else []
    ctx.ensure_object(dict)
    ctx.obj["timeout"] = timeout
    ctx.obj["parallel"] = parallel
    ctx.obj["brew_token"] = brew_token
    ctx.obj["api_host"] = api_host
    ctx.obj["rosa"] = _rosa

    if debug:
        os.environ["OCM_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
        os.environ["OPENSHIFT_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"

    _client = OCMPythonClient(
        token=token,
        endpoint=endpoint,
        api_host=api_host,
        discard_unknown_keys=True,
    ).client

    addons_dict = {}
    for _addon in addons:
        addon_name, addon_parameters = extract_operator_addon_params(
            resource_and_parameters=_addon, resource_type="addon"
        )
        addons_dict.setdefault(addon_name, {})["parameters"] = addon_parameters
        addons_dict[addon_name]["cluster_addon"] = ClusterAddOn(
            client=_client, cluster_name=cluster, addon_name=addon_name
        )

    ctx.obj["addons_dict"] = addons_dict
    if any(addon_name not in addons_dict.keys() for addon_name in _rosa):
        click.echo(
            f"""
An addon indicated with --rosa does not match any of addons names that were given.
Addons to install/uninstall: {', '.join(addons_dict.keys())}.
Addons to use with rosa: {', '.join(_rosa)}.
"""
        )
        raise click.Abort()


@addon.command()
@click.pass_context
def install(ctx):
    """Install cluster Addons."""
    run_action(
        action="install_addon",
        addons=ctx.obj["addons_dict"],
        parallel=ctx.obj["parallel"],
        timeout=ctx.obj["timeout"],
        brew_token=ctx.obj["brew_token"],
        api_host=ctx.obj["api_host"],
        rosa=ctx.obj["rosa"],
    )


@addon.command()
@click.pass_context
def uninstall(ctx):
    """Uninstall cluster Addons."""
    run_action(
        action="uninstall_addon",
        addons=ctx.obj["addons_dict"],
        parallel=ctx.obj["parallel"],
        timeout=ctx.obj["timeout"],
        rosa=ctx.obj["rosa"],
    )
