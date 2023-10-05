import multiprocessing
import os

import click
from ocp_utilities.infra import get_client
from ocp_utilities.operators import install_operator, uninstall_operator

from ocp_addons_operators_cli.constants import TIMEOUT_30MIN
from ocp_addons_operators_cli.utils import extract_iibs_from_json, set_debug_os_flags


def _client(ctx):
    return get_client(config_file=ctx.obj["kubeconfig"])


def run_action(
    client, action, operators_tuple, parallel, brew_token=None, iib_dict=None
):
    jobs = []
    iib_dict = iib_dict or {}

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
            kwargs["iib_index_image"] = _operator.get(
                "iib", iib_dict.get(operator_name)
            )
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


def install(ctx):
    """Install cluster Operator."""
    ocp_version = os.environ.get("OCP_VERSION")
    job_name = (
        os.environ.get("JOB_NAME")
        if os.environ.get("INSTALL_FROM_IIB") == "true"
        else None
    )
    iib_dict = {}
    if ocp_version and job_name:
        iib_dict = extract_iibs_from_json(ocp_version=ocp_version, job_name=job_name)

    run_action(
        client=_client(ctx=ctx),
        action="install_operator",
        operators_tuple=ctx.obj["operators_tuple"],
        parallel=ctx.obj["parallel"],
        brew_token=ctx.obj["brew_token"],
        iib_dict=iib_dict,
    )


def uninstall(ctx):
    """Uninstall cluster Operator."""
    run_action(
        client=_client(ctx=ctx),
        action="uninstall_operator",
        operators_tuple=ctx.obj["operators_tuple"],
        parallel=ctx.obj["parallel"],
    )
