import ast
import multiprocessing
import os

import click
from constants import TIMEOUT_30MIN
from ocp_utilities.infra import get_client
from ocp_utilities.operators import install_operator, uninstall_operator


def _client(ctx):
    return get_client(config_file=ctx.obj["kubeconfig"])


def run_action(client, action, operators, parallel, timeout):
    jobs = []

    operators_action = (
        install_operator if action == "install_operator" else uninstall_operator
    )
    for operator_name, operator_params in operators.items():
        kwargs = {"admin_client": client, "name": operator_name, "timeout": timeout}
        if action == "install_operator":
            kwargs["channel"] = operator_params.get("channel", "stable")
            kwargs["source"] = operator_params.get("source", "redhat-operators")
            kwargs["operator_namespace"] = operator_params.get("namespace")
            kwargs["target_namespaces"] = (
                operator_params["target-namespaces"].split("..")
                if operator_params.get("target-namespaces")
                else None
            )

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
    "--operators",
    help="""
    \b
    Operators to install.
    Format to pass is 'operators_name_1|param1=1,param2=2'
    Optional parameters:
        namespace - Operator namespace
        channel - Operator channel to install from, default: 'stable'
        source - Operator source, default: 'redhat-operators'
        target-namespaces - A double-dotter string with target namespaces for the operator, example: ns1..ns2
    \b
    """,
    required=True,
    multiple=True,
)
@click.option(
    "-p",
    "--parallel",
    help="Run operator install/uninstall in parallel",
    default="false",
    type=click.Choice(["true", "false"]),
    show_default=True,
)
@click.option("--debug", help="Enable debug logs", is_flag=True)
@click.option(
    "--timeout",
    help="Timeout in seconds to wait for operator to be installed/uninstalled",
    default=TIMEOUT_30MIN,
    show_default=True,
)
@click.option(
    "--kubeconfig",
    help="Path to kubeconfig file",
    required=True,
    default=os.environ.get("KUBECONFIG"),
    type=click.Path(exists=True),
    show_default=True,
)
@click.pass_context
def operator(ctx, kubeconfig, debug, timeout, operators, parallel):
    """
    Command line to Install/Uninstall Operator on OCP cluster.
    """
    ctx.ensure_object(dict)
    ctx.obj["operators"] = operators
    ctx.obj["timeout"] = timeout
    ctx.obj["kubeconfig"] = kubeconfig
    ctx.obj["parallel"] = ast.literal_eval(parallel.capitalize())
    if debug:
        os.environ["OCM_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
        os.environ["OPENSHIFT_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"

    operators_dict = {}
    for _operator in [__operator for __operator in operators if __operator]:
        operator_parameters = {}
        operator_and_params = _operator.split("|")
        operator_name = operator_and_params[0]

        if len(operator_and_params) > 1:
            parameters = operator_and_params[-1].split(",")
            parameters = [_param.strip() for _param in parameters]
            for parameter in parameters:
                if "=" not in parameter:
                    click.echo(f"parameters should be id=value, got {parameter}\n")
                    raise click.Abort()

                param_name, param_value = parameter.split("=")
                operator_parameters[param_name] = param_value
            operators_dict[operator_name] = operator_parameters

    ctx.obj["operators_dict"] = operators_dict


@operator.command()
@click.pass_context
def install(ctx):
    """Install cluster Operator."""
    run_action(
        client=_client(ctx=ctx),
        action="install_operator",
        operators=ctx.obj["operators_dict"],
        parallel=ctx.obj["parallel"],
        timeout=ctx.obj["timeout"],
    )


@operator.command()
@click.pass_context
def uninstall(ctx):
    """Uninstall cluster Operator."""
    run_action(
        client=_client(ctx=ctx),
        action="uninstall_operator",
        operators=ctx.obj["operators_dict"],
        parallel=ctx.obj["parallel"],
        timeout=ctx.obj["timeout"],
    )
