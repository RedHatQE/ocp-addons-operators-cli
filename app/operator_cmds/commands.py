import multiprocessing
import os

import click
from click_dict_type import DictParamType
from constants import TIMEOUT_30MIN
from ocp_utilities.infra import get_client
from ocp_utilities.operators import install_operator, uninstall_operator
from utils import set_debug_os_flags


def _client(ctx):
    return get_client(config_file=ctx.obj["kubeconfig"])


def run_action(client, action, operators_tuple, parallel, brew_token=None):
    jobs = []

    operators_action = (
        install_operator if action == "install_operator" else uninstall_operator
    )
    for _operator in operators_tuple:
        operator_name = _operator["name"]
        kwargs = {
            "admin_client": client,
            "name": operator_name,
            "timeout": _operator.get("timeout", TIMEOUT_30MIN),
            "operator_namespace": _operator.get("namespace"),
        }
        if brew_token:
            kwargs["brew_token"] = brew_token

        if action == "install_operator":
            kwargs["channel"] = _operator.get("channel", "stable")
            kwargs["source"] = _operator.get("source", "redhat-operators")
            kwargs["iib_index_image"] = _operator.get("iib")
            kwargs["target_namespaces"] = _operator.get("target-namespaces")

        if parallel:
            job = multiprocessing.Process(
                name=f"{operator_name}---{action}",
                target=operators_action,
                kwargs=kwargs,
            )
            jobs.append(job)
            job.start()
        else:
            operators_action(**kwargs)

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
    required=True,
    multiple=True,
)
@click.option(
    "-p",
    "--parallel",
    help="Run operator install/uninstall in parallel",
    is_flag=True,
    show_default=True,
)
@click.option("--debug", help="Enable debug logs", is_flag=True)
@click.option(
    "--kubeconfig",
    help="Path to kubeconfig file",
    required=True,
    default=os.environ.get("KUBECONFIG"),
    type=click.Path(exists=True),
    show_default=True,
)
@click.option(
    "--brew-token",
    help="""
    \b
    Brew token (needed to install operator using IIB).
    Default value is taken from environment variable, else will be taken from --brew-token flag.
    """,
    required=False,
    default=os.environ.get("BREW_TOKEN"),
)
@click.pass_context
def operators(ctx, kubeconfig, debug, operator, parallel, brew_token):
    """
    Command line to Install/Uninstall Operator on OCP cluster.
    """
    ctx.ensure_object(dict)
    ctx.obj["operators_tuple"] = operator
    ctx.obj["kubeconfig"] = kubeconfig
    ctx.obj["parallel"] = parallel
    ctx.obj["brew_token"] = brew_token
    if debug:
        set_debug_os_flags()


@operators.command()
@click.pass_context
def install(ctx):
    """Install cluster Operator."""
    run_action(
        client=_client(ctx=ctx),
        action="install_operator",
        operators_tuple=ctx.obj["operators_tuple"],
        parallel=ctx.obj["parallel"],
        brew_token=ctx.obj["brew_token"],
    )


@operators.command()
@click.pass_context
def uninstall(ctx):
    """Uninstall cluster Operator."""
    run_action(
        client=_client(ctx=ctx),
        action="uninstall_operator",
        operators_tuple=ctx.obj["operators_tuple"],
        parallel=ctx.obj["parallel"],
    )
