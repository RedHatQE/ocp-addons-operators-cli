import os

import click
from constants import TIMEOUT_30MIN
from ocp_utilities.infra import get_client
from ocp_utilities.operators import install_operator, uninstall_operator


def _client(ctx):
    return get_client(config_file=ctx.obj["kubeconfig"])


@click.group()
@click.option("--debug", help="Enable debug logs", is_flag=True)
@click.option(
    "--timeout",
    help="Timeout in seconds to wait for addon to be installed/uninstalled",
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
@click.option("-n", "--name", help="Operator name to install/uninstall", required=True)
@click.option("-ns", "--namespace", help="Operator namespace", required=False)
@click.pass_context
def operator(ctx, kubeconfig, name, debug, timeout, namespace):
    """
    Command line to Install/Uninstall Operator on OCP cluster.
    """
    ctx.ensure_object(dict)
    ctx.obj["name"] = name
    ctx.obj["timeout"] = timeout
    ctx.obj["kubeconfig"] = kubeconfig
    ctx.obj["namespace"] = namespace
    if debug:
        os.environ["OCM_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
        os.environ["OPENSHIFT_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"


@operator.command()
@click.option(
    "-c",
    "--channel",
    help="Operator channel to install from",
    default="stable",
    show_default=True,
)
@click.option(
    "-s",
    "--source",
    help="Catalog source name install from",
    default="redhat-operators",
    show_default=True,
)
@click.option(
    "--target-namespaces",
    help="target namespaces for the operator. comma separated string",
)
@click.pass_context
def install(ctx, channel, source, target_namespaces):
    """Install cluster Operator."""
    client = _client(ctx=ctx)
    name = ctx.obj["name"]
    timeout = ctx.obj["timeout"]
    namespace = ctx.obj["namespace"]

    _target_namespaces = None
    if target_namespaces:
        _target_namespaces = target_namespaces.split(",")

    install_operator(
        admin_client=client,
        name=name,
        channel=channel,
        source=source,
        target_namespaces=_target_namespaces,
        timeout=timeout,
        operator_namespace=namespace,
    )


@operator.command()
@click.pass_context
def uninstall(ctx):
    """Uninstall cluster Operator."""
    name = ctx.obj["name"]
    client = _client(ctx=ctx)
    timeout = ctx.obj["timeout"]

    uninstall_operator(admin_client=client, name=name, timeout=timeout)
