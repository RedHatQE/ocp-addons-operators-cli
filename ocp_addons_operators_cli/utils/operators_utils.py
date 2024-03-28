import os

import click
import yaml
from ocp_utilities.infra import get_client
from ocp_utilities.operators import install_operator, uninstall_operator
from ocp_utilities.cluster_versions import get_cluster_version
from simple_logger.logger import get_logger

from ocp_addons_operators_cli.constants import TIMEOUT_60MIN
from ocp_addons_operators_cli.utils.general import (
    get_operator_iib,
    get_operators_iibs_config_from_json,
    tts,
)

LOGGER = get_logger(name=__name__)


def get_operators_from_user_input(**kwargs):
    LOGGER.info("Get operators data from user input.")
    # From CLI, we get `operator` tuple, from YAML file we get `operators` list
    operators = [*kwargs.get("operator")] or kwargs.get("operators", [])

    for operator in operators:
        # Get kubeconfig from global config if not passed as operator config
        if not operator.get("kubeconfig"):
            operator["kubeconfig"] = kwargs.get("kubeconfig")
        operator["brew-token"] = kwargs.get("brew_token")

    return operators


def assert_missing_kubeconfig_from_user_input(operators):
    LOGGER.info("Verify `kubeconfig` is not missing from user input.")
    operators_missing_kubeconfig = [operator["name"] for operator in operators if operator["kubeconfig"] is None]
    if operators_missing_kubeconfig:
        LOGGER.error(
            "The following operators are missing `kubeconfig`:"
            f" {operators_missing_kubeconfig}. Either add to operator config or"
            " pass `--kubeconfig`"
        )
        raise click.Abort()


def assert_missing_kubeconfig_file(operators):
    LOGGER.info("Verify `kubeconfig` file(s) exist.")
    operator_non_existing_kubeconfig = [
        operator["name"] for operator in operators if not os.path.exists(operator["kubeconfig"])
    ]

    if operator_non_existing_kubeconfig:
        LOGGER.error("The following operators kubeconfig file does not exist: {operator_non_existing_kubeconfig}")
        raise click.Abort()


def assert_missing_token_for_iib_installation(operators, brew_token):
    LOGGER.info("Verify `brew token` is not missing from user input for operators IIB installation.")
    operators_iib_missing_token = [operator["name"] for operator in operators if operator.get("iib") and not brew_token]
    if operators_iib_missing_token:
        LOGGER.error(
            "The following operators will be installed using IIB:"
            " {operators_iib_missing_token}.`--brew-token` must be provided for"
            " operator installation using IIB."
        )
        raise click.Abort()


def assert_operators_user_input(operators, brew_token):
    if operators:
        LOGGER.info("Verify operators data from user input.")
        assert_missing_kubeconfig_from_user_input(operators=operators)
        assert_missing_kubeconfig_file(operators=operators)
        assert_missing_token_for_iib_installation(operators=operators, brew_token=brew_token)


def get_cluster_name_from_kubeconfig(kubeconfig, operator_name):
    LOGGER.info("Get cluster name from kubeconfig.")
    with open(kubeconfig) as fd:
        kubeconfig = yaml.safe_load(fd)

    kubeconfig_clusters = kubeconfig["clusters"]
    if len(kubeconfig_clusters) > 1:
        LOGGER.error(f"Operator: {operator_name} kubeconfig file contains more than one cluster.")
        raise click.Abort()

    return kubeconfig_clusters[0]["name"]


def get_operator_iib_from_iib_dict(iib_dict, operator_dict, job_name=None):
    if iib := operator_dict.get("iib"):
        return iib

    if not job_name:
        return None

    cluster_version = get_cluster_version(client=operator_dict["ocp-client"])
    cluster_version_major_minor = f"{cluster_version.major}.{cluster_version.minor}"

    return get_operator_iib(
        iib_dict=iib_dict,
        ocp_version=cluster_version_major_minor,
        job_name=job_name,
        operator_name=operator_dict["name"],
    )


def prepare_operators(operators, install, user_kwargs_dict):
    """
    Update operator dict with additional data for install or uninstall

    Args:
        operators (list): list of operators dicts
        install (bool): install or uninstall action
        user_kwargs_dict (dict): dict with user kwargs

    Returns:
        list: updated list of operators dicts

    """
    LOGGER.info("Preparing operators dict")

    iib_dict = None
    job_name = None

    if install:
        s3_bucket_operators_latest_iib_path = user_kwargs_dict.get("s3_bucket_operators_latest_iib_path")
        local_operators_latest_iib_path = user_kwargs_dict.get("local_operators_latest_iib_path")

        if s3_bucket_operators_latest_iib_path or local_operators_latest_iib_path:
            iib_dict = get_operators_iibs_config_from_json(
                s3_bucket_operators_latest_iib_path=s3_bucket_operators_latest_iib_path,
                aws_region=user_kwargs_dict.get("aws_region"),
                local_operators_latest_iib_path=local_operators_latest_iib_path,
            )

            job_name = os.environ.get("PARENT_JOB_NAME", os.environ.get("JOB_NAME"))

    # import ipdb
    #
    # ipdb.set_trace()
    for operator in operators:
        kubeconfig = operator["kubeconfig"]
        operator["ocp-client"] = get_client(config_file=kubeconfig)
        operator["cluster-name"] = get_cluster_name_from_kubeconfig(
            kubeconfig=kubeconfig,
            operator_name=operator["name"],
        )
        operator["timeout"] = tts(ts=operator.get("timeout", TIMEOUT_60MIN))
        operator["must_gather_output_dir"] = user_kwargs_dict.get("must_gather_output_dir")

        if install:
            operator["channel"] = operator.get("channel", "stable")
            operator["source"] = operator.get("source", "redhat-operators")
            operator["iib_index_image"] = get_operator_iib_from_iib_dict(
                iib_dict=iib_dict, job_name=job_name, operator_dict=operator
            )

    return operators


def prepare_operators_action(operators, install):
    operators_action_list = []
    operator_func = install_operator if install else uninstall_operator

    for operator in operators:
        name = operator["name"]
        LOGGER.info(f"Preparing operator: {name}, func: {operator_func.__name__}")
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
            action_kwargs["iib_index_image"] = operator.get("iib_index_image")
            action_kwargs["source_image"] = operator.get("source-image")
            action_kwargs["target_namespaces"] = operator.get("target-namespaces")
            if must_gather_output_dir := operator.get("must_gather_output_dir"):
                action_kwargs["must_gather_output_dir"] = must_gather_output_dir
                action_kwargs["kubeconfig"] = operator["kubeconfig"]
                action_kwargs["cluster_name"] = operator["cluster-name"]

        operators_action_list.append((operator_func, action_kwargs))

    return operators_action_list
