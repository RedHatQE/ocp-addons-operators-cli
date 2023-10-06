import os

import click
import yaml
from ocp_utilities.infra import get_client
from ocp_utilities.operators import install_operator, uninstall_operator

from ocp_addons_operators_cli.constants import OPERATOR_STR, TIMEOUT_60MIN
from ocp_addons_operators_cli.utils.general import click_echo, get_iib_dict, tts


def get_operators_from_user_input(**kwargs):
    # From CLI, we get `operator`, from YAML file we get `operators`
    operators = kwargs.get("operator", [])
    if not operators:
        operators = kwargs.get("operators", [])

    for operator in operators:
        if not operator.get("kubeconfig"):
            operator["kubeconfig"] = kwargs.get("kubeconfig")
        operator["brew-token"] = kwargs.get("brew_token")

    return operators


def assert_operators_user_input(operators, section):
    if operators:
        operators_missing_kubeconfig = [
            operator["name"] for operator in operators if operator["kubeconfig"] is None
        ]
        if operators_missing_kubeconfig:
            click_echo(
                name=operators_missing_kubeconfig,
                product=OPERATOR_STR,
                section=section,
                msg=(
                    "`kubeconfig` is missing. Either add to operator config or pass"
                    " `--kubeconfig`"
                ),
                error=True,
            )
            raise click.Abort()

        operator_non_existing_kubeconfig = [
            operator["name"]
            for operator in operators
            if not os.path.exists(operator["kubeconfig"])
        ]

        if operator_non_existing_kubeconfig:
            click_echo(
                name=operator_non_existing_kubeconfig,
                product=OPERATOR_STR,
                section=section,
                msg="`kubeconfig` file does not exist.",
                error=True,
            )
            raise click.Abort()


def get_cluster_name_from_kubeconfig(kubeconfig, operator_name):
    with open(kubeconfig) as fd:
        kubeconfig = yaml.safe_load(fd)

    kubeconfig_clusters = kubeconfig["clusters"]
    if len(kubeconfig_clusters) > 1:
        click_echo(
            name=operator_name,
            product=OPERATOR_STR,
            section="Prepare operators",
            msg="Kubeconfig file contains more than one cluster.",
            error=True,
        )
        raise click.Abort()

    return kubeconfig_clusters[0]["name"]


def prepare_operators(operators, brew_token, install):
    for operator in operators:
        kubeconfig = operator["kubeconfig"]
        operator["ocp-client"] = get_client(config_file=kubeconfig)
        operator["cluster-name"] = get_cluster_name_from_kubeconfig(
            kubeconfig=kubeconfig, operator_name=operator["name"]
        )
        operator["timeout"] = tts(ts=operator.get("timeout", TIMEOUT_60MIN))

        if install:
            operator["channel"] = operator.get("channel", "stable")
            operator["source"] = operator.get("source", "redhat-operators")
            operator["brew-token"] = brew_token

            iib_dict = get_iib_dict()
            operator["iib_index_image"] = operator.get(
                "iib", iib_dict.get(operator["name"])
            )

    return operators


def run_operator_action(operators, install, section, parallel, executor):
    futures = []
    processed_results = []
    operator_func = install_operator if install else uninstall_operator

    for operator in operators:
        name = operator["name"]
        action_kwargs = {
            "admin_client": operator["ocp-client"],
            "name": name,
            "timeout": operator["timeout"],
            "operator_namespace": operator.get("namespace"),
        }

        if install:
            brew_token = operator.get("brew-token")
            if brew_token:
                action_kwargs["brew_token"] = brew_token
            action_kwargs["channel"] = operator["channel"]
            action_kwargs["source"] = operator["source"]
            action_kwargs["iib_index_image"] = operator.get("iib")
            action_kwargs["target_namespaces"] = operator.get("target-namespaces")

        # TODO add cluster name
        click_echo(
            cluster_name=operator["cluster-name"],
            name=name,
            product=OPERATOR_STR,
            section=section,
            msg=f"[parallel: {parallel}]",
        )

        if parallel:
            futures.append(executor.submit(operator_func, **action_kwargs))
        else:
            processed_results.append(operator_func(**action_kwargs))

    return futures, processed_results
