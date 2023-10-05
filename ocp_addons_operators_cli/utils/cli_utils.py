import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
from ocm_python_client.exceptions import NotFoundException
from ocm_python_wrapper.cluster import Cluster, ClusterAddOn
from ocm_python_wrapper.ocm_client import OCMPythonClient
from ocp_utilities.infra import get_client
from ocp_utilities.operators import install_operator, uninstall_operator

from ocp_addons_operators_cli.constants import (
    ADDON_STR,
    OPERATOR_STR,
    PRODUCTION_STR,
    STAGE_STR,
    SUPPORTED_ACTIONS,
    TIMEOUT_60MIN,
)
from ocp_addons_operators_cli.utils.addon_utils import extract_addon_params
from ocp_addons_operators_cli.utils.general import (
    click_echo,
    get_iib_dict,
    set_debug_os_flags,
    tts,
)

NO_PRODUCT_NAME_FOR_LOG = "All"


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


def get_addons_from_user_input(**kwargs):
    # From CLI, we get `addon`, from YAML file we get `addons`
    addons = kwargs.get("addon", [])
    if not addons:
        addons = kwargs.get("addons", [])

    for addon in addons:
        if not addon.get("cluster-name"):
            addon["cluster-name"] = kwargs.get("cluster_name")

    return addons


def abort_no_ocm_token(ocm_token, addons, section):
    if addons and not ocm_token:
        click_echo(
            name=NO_PRODUCT_NAME_FOR_LOG,
            product=ADDON_STR,
            section=section,
            msg="`--ocm-token` is required for addon installation",
            error=True,
        )
        raise click.Abort()


def assert_operators_user_input(operators, section):
    if operators:
        operators_missing_kubeconfig = [
            operator["name"] for operator in operators if operator["kubeconfig"] is None
        ]
        if operators_missing_kubeconfig:
            click_echo(
                name=NO_PRODUCT_NAME_FOR_LOG,
                product=OPERATOR_STR,
                section=section,
                msg=(
                    f"`kubeconfig` is missing for {operators_missing_kubeconfig}."
                    " Either add to operator config or pass `--kubeconfig`"
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
                name=NO_PRODUCT_NAME_FOR_LOG,
                product=OPERATOR_STR,
                section=section,
                msg=(
                    "`kubeconfig` file does not exist for"
                    f" {operators_missing_kubeconfig}."
                ),
                error=True,
            )
            raise click.Abort()


def assert_addons_user_input(addons, section):
    if addons:
        addons_missing_cluster_name = [
            addon["name"] for addon in addons if not addon.get("cluster-name")
        ]
        if addons_missing_cluster_name:
            click_echo(
                name=NO_PRODUCT_NAME_FOR_LOG,
                product=ADDON_STR,
                section=section,
                msg=(
                    f"`cluster-name` is missing for {addons_missing_cluster_name}."
                    " Either add to addon config or pass `--cluster-name`"
                ),
                error=True,
            )
            raise click.Abort()

        supported_envs = [STAGE_STR, PRODUCTION_STR]
        addons_wrong_env = [
            addon["name"]
            for addon in addons
            if (
                ocm_env := addon.get("ocm-evn")  # noqa
                and ocm_env not in supported_envs  # noqa
            )
        ]
        if addons_wrong_env:
            click_echo(
                name=NO_PRODUCT_NAME_FOR_LOG,
                product=ADDON_STR,
                section=section,
                msg=(
                    f"Addons {addons_wrong_env} have wrong OCM environment. Supported"
                    f" envs: {supported_envs}"
                ),
                error=True,
            )
            raise click.Abort()


def verify_user_input(**kwargs):
    action = kwargs.get("action")
    operators = kwargs.get("operators")
    addons = kwargs.get("addons")
    kwargs.get("brew_token")
    ocm_token = kwargs.get("ocm_token")

    section = "Verify user input"
    abort_no_ocm_token(ocm_token=ocm_token, addons=addons, section=section)

    if not action:
        click_echo(
            name=NO_PRODUCT_NAME_FOR_LOG,
            product=NO_PRODUCT_NAME_FOR_LOG,
            section=section,
            msg=f"'action' must be provided, supported actions: `{SUPPORTED_ACTIONS}`",
            error=True,
        )
        raise click.Abort()

    if action not in SUPPORTED_ACTIONS:
        click_echo(
            name=NO_PRODUCT_NAME_FOR_LOG,
            product=NO_PRODUCT_NAME_FOR_LOG,
            section=section,
            msg=(
                f"'{action}' is not supported, supported actions: `{SUPPORTED_ACTIONS}`"
            ),
            error=True,
        )
        raise click.Abort()

    if not (operators or addons):
        click_echo(
            name=NO_PRODUCT_NAME_FOR_LOG,
            product=NO_PRODUCT_NAME_FOR_LOG,
            section=section,
            msg="At least one '--operator' oe `--addon` option must be provided.",
            error=True,
        )
        raise click.Abort()

    assert_operators_user_input(operators=operators, section=section)
    assert_addons_user_input(addons=addons, section=section)


def prepare_operators(operators, brew_token, install):
    for operator in operators:
        # TODO: add cluster name
        operator["ocp-client"] = get_client(config_file=operator["kubeconfig"])
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


def prepare_addons(addons, ocm_token, endpoint, brew_token, install):
    for addon in addons:
        addon_name = addon["name"]
        addon["wait_timeout"] = tts(ts=addon.get("timeout", TIMEOUT_60MIN))
        ocm_env = addon.get("ocm-env", STAGE_STR)
        addon["ocm-env"] = ocm_env
        addon["brew-token"] = brew_token
        addon["rosa"] = bool(addon.get("rosa"))

        ocm_client = OCMPythonClient(
            token=ocm_token,
            endpoint=endpoint,
            api_host=ocm_env,
            discard_unknown_keys=True,
        ).client
        addon["ocm-client"] = ocm_client
        addon["cluster-object"] = Cluster(
            client=ocm_client,
            name=addon_name,
        )

        if install:
            addon["parameters"] = extract_addon_params(addon_dict=addon)

            cluster_name = addon["cluster-name"]
            try:
                addon["cluster_addon"] = ClusterAddOn(
                    client=ocm_client, cluster_name=cluster_name, addon_name=addon_name
                )
            except NotFoundException as exc:
                click_echo(
                    name=addon_name,
                    product=ADDON_STR,
                    section="Prepare addon config",
                    msg=f"Failed to get addon for cluster {cluster_name} {exc}.",
                    error=True,
                )
                raise click.Abort()

            if addon_name == "managed-odh" and ocm_env == STAGE_STR:
                if brew_token:
                    addon["brew-token"] = brew_token
                else:
                    # TODO: remove to veify?
                    click_echo(
                        name=addon_name,
                        product=ADDON_STR,
                        section="Prepare addon config",
                        msg=(
                            f"--brew-token flag for {addon_name} addon install is"
                            " missing"
                        ),
                        error=True,
                    )
                    raise click.Abort()

    return addons


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


def run_addons_action(addons, install, section, parallel, executor):
    futures = []
    processed_results = []
    addon_func = ClusterAddOn.install_addon if install else ClusterAddOn.uninstall_addon

    for addon in addons:
        name = addon["name"]
        action_kwargs = {
            "wait": True,
            "wait_timeout": addon["wait_timeout"],
            "rosa": addon["rosa"],
        }
        if install:
            action_kwargs["parameters"] = addon["parameters"]
            brew_token = addon.get("brew-token")
            if brew_token:
                action_kwargs["brew_token"] = brew_token

        click_echo(
            name=name,
            product=ADDON_STR,
            section=section,
            msg=f"[parallel: {parallel}]",
        )

        if parallel:
            futures.append(executor.submit(addon_func(), **action_kwargs))
        else:
            processed_results.append(addon_func(**action_kwargs))

        return futures, processed_results


def run_install_or_uninstall_products(operators, addons, parallel, debug, install):
    if debug:
        set_debug_os_flags()

    futures = []
    processed_results = []
    section = f"{'Install' if install else 'Uninstall'}"

    with ThreadPoolExecutor() as executor:
        if operators:
            operators_futures, operators_processed_results = run_operator_action(
                operators=operators,
                install=install,
                section=section,
                parallel=parallel,
                executor=executor,
            )
            futures.append(operators_futures)
            processed_results.append(operators_processed_results)

        if addons:
            addons_futures, addons_processed_results = run_addons_action(
                addons=addons,
                install=install,
                section=section,
                parallel=parallel,
                executor=executor,
            )
            futures.append(addons_futures)
            processed_results.append(addons_processed_results)

    if futures:
        for result in as_completed(futures):
            if result.exception():
                click_echo(
                    name="XXX",  # TODO: get from thread
                    product="XXX",  # TODO: get from thread
                    section=section,
                    msg=f"Failed to run: {result.exception()}\n",
                    error=True,
                )
                raise click.Abort()
