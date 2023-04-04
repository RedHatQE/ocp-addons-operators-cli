import ast
import multiprocessing
import os

import click
from constants import TIMEOUT_30MIN
from ocm_python_wrapper.cluster import ClusterAddOn
from ocm_python_wrapper.ocm_client import OCMPythonClient


def run_action(action, addons, parallel, timeout):
    jobs = []
    for values in addons.values():
        cluster_addon_obj = values["cluster_addon"]
        addon_action_func = getattr(cluster_addon_obj, action)
        _args = [True, timeout]
        if action == "install_addon":
            _args.insert(0, values["parameters"])

        if parallel:
            job = multiprocessing.Process(
                name=f"{cluster_addon_obj.addon_name}---{action}",
                target=addon_action_func,
                args=tuple(_args),
            )
            jobs.append(job)
            job.start()
        else:
            addon_action_func(*_args)

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
    Format to pass is 'addon_name_1|param1=1,param2=2'\b
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
    default="false",
    type=click.Choice(["true", "false"]),
    show_default=True,
)
@click.pass_context
def addon(ctx, addons, token, api_host, cluster, endpoint, timeout, debug, parallel):
    """
    Command line to Install/Uninstall Addons on OCM managed cluster.
    """
    ctx.ensure_object(dict)
    ctx.obj["timeout"] = timeout
    ctx.obj["parallel"] = ast.literal_eval(parallel.capitalize())
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
    for _addon in [__addon for __addon in addons if __addon]:
        addon_parameters = []
        addon_and_params = _addon.split("|")
        addon_name = addon_and_params[0]
        addons_dict[addon_name] = {}

        if len(addon_and_params) > 1:
            parameters = addon_and_params[-1].split(",")
            parameters = [_param.strip() for _param in parameters]
            for parameter in parameters:
                if "=" not in parameter:
                    click.echo(f"parameters should be id=value, got {parameter}\n")
                    raise click.Abort()

                _id, _value = parameter.split("=")
                addon_parameters.append({"id": _id, "value": _value})

        addons_dict[addon_name]["parameters"] = addon_parameters
        addons_dict[addon_name]["cluster_addon"] = ClusterAddOn(
            client=_client, cluster_name=cluster, addon_name=addon_name
        )

    ctx.obj["addons_dict"] = addons_dict


@addon.command()
@click.pass_context
def install(ctx):
    """Install cluster Addons."""
    run_action(
        action="install_addon",
        addons=ctx.obj["addons_dict"],
        parallel=ctx.obj["parallel"],
        timeout=ctx.obj["timeout"],
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
    )
