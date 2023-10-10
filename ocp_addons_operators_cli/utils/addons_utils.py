import click
from ocm_python_client.exceptions import NotFoundException
from ocm_python_wrapper.cluster import Cluster, ClusterAddOn
from ocm_python_wrapper.ocm_client import OCMPythonClient
from simple_logger.logger import get_logger

from ocp_addons_operators_cli.constants import PRODUCTION_STR, STAGE_STR, TIMEOUT_30MIN
from ocp_addons_operators_cli.utils.general import tts

LOGGER = get_logger(name=__name__)


def extract_addon_params(addon_dict):
    """
    Extract addon parameters from user input

    Args:
        addon_dict (dict): dict constructed from addon user input

    Returns:
        list: list of addon parameters dicts

    """
    exclude_list = [
        "cluster-addon",
        "name",
        "timeout",
        "rosa",
        "ocm-client",
        "cluster-object",
        "ocm-env",
        "brew-token",
        "cluster-name",
    ]
    resource_parameters = []

    for key, value in addon_dict.items():
        if key in exclude_list:
            continue

        resource_parameters.append({"id": key, "value": value})

    return resource_parameters


def get_addons_from_user_input(**kwargs):
    LOGGER.info("Get addon parameters from user input.")
    # From CLI, we get `addon`, from YAML file we get `addons`
    addons = kwargs.get("addon", [])
    if not addons:
        addons = kwargs.get("addons", [])

    for addon in addons:
        if not addon.get("cluster-name"):
            addon["cluster-name"] = kwargs.get("cluster_name")

    return addons


def assert_addons_user_input(addons, brew_token):
    if addons:
        LOGGER.info("Verify addons data from user input.")
        addons_missing_cluster_name = [
            addon["name"] for addon in addons if not addon.get("cluster-name")
        ]
        if addons_missing_cluster_name:
            LOGGER.error(
                f"For addons {addons_missing_cluster_name} `cluster-name` is missing. "
                "Either add to addon config or pass `--cluster-name`"
            )
            raise click.Abort()

        supported_envs = [STAGE_STR, PRODUCTION_STR]
        addons_wrong_env = [
            addon["name"] for addon in addons if addon.get("ocm-evn") in supported_envs
        ]
        if addons_wrong_env:
            LOGGER.error(
                f"Addons {addons_wrong_env} have wrong OCM environment. Supported envs:"
                f" {supported_envs}"
            )
            raise click.Abort()

        managed_odh_str = "managed-odh"
        if (
            any(
                [
                    addon["name"] == managed_odh_str and addon["ocm-env"] == STAGE_STR
                    for addon in addons
                ]
            )
            and not brew_token
        ):
            LOGGER.error(
                f"{managed_odh_str} addon on {STAGE_STR} requires brew token. Pass"
                " `--brew-token`"
            )
            raise click.Abort()


def prepare_addons(addons, ocm_token, endpoint, brew_token, install):
    missing_clusters_addons = []
    for addon in addons:
        addon_name = addon["name"]
        cluster_name = addon["cluster-name"]
        addon["timeout"] = tts(ts=addon.get("timeout", TIMEOUT_30MIN))
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
        cluster = Cluster(
            client=ocm_client,
            name=addon_name,
        )
        if cluster.exists:
            addon["cluster-object"] = cluster
        else:
            missing_clusters_addons.append(addon_name)

        try:
            addon["cluster-addon"] = ClusterAddOn(
                client=ocm_client, cluster_name=cluster_name, addon_name=addon_name
            )
        except NotFoundException as exc:
            LOGGER.error(f"Failed to get addon for cluster {cluster_name} on {exc}.")
            raise click.Abort()

        if install:
            addon["parameters"] = extract_addon_params(addon_dict=addon)

    if missing_clusters_addons:
        LOGGER.error(f"Addons {missing_clusters_addons} cluster do not exist.")

    return addons


def prepare_addons_action(addons, install):
    addons_action_list = []

    for addon in addons:
        addon_obj = addon["cluster-addon"]
        addon_func = addon_obj.install_addon if install else addon_obj.uninstall_addon
        name = addon["name"]
        LOGGER.info(f"Preparing addon {name} func {addon_func}")

        action_kwargs = {
            "wait": True,
            "wait_timeout": addon["timeout"],
            "rosa": addon["rosa"],
        }
        if install:
            action_kwargs["parameters"] = addon["parameters"]
            brew_token = addon.get("brew-token")
            if brew_token:
                action_kwargs["brew_token"] = brew_token

        addons_action_list.append((addon_func, action_kwargs))

    return addons_action_list
