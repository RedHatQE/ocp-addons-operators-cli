import click
from ocm_python_client.exceptions import NotFoundException
from ocm_python_wrapper.cluster import Cluster, ClusterAddOn
from ocm_python_wrapper.ocm_client import OCMPythonClient

from ocp_addons_operators_cli.constants import (
    ADDON_STR,
    PRODUCTION_STR,
    STAGE_STR,
    TIMEOUT_30MIN,
)
from ocp_addons_operators_cli.utils.general import click_echo, tts


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
    # From CLI, we get `addon`, from YAML file we get `addons`
    addons = kwargs.get("addon", [])
    if not addons:
        addons = kwargs.get("addons", [])

    for addon in addons:
        if not addon.get("cluster-name"):
            addon["cluster-name"] = kwargs.get("cluster_name")

    return addons


def assert_addons_user_input(addons, section):
    if addons:
        addons_missing_cluster_name = [
            addon["name"] for addon in addons if not addon.get("cluster-name")
        ]
        if addons_missing_cluster_name:
            click_echo(
                name=addons_missing_cluster_name,
                product=ADDON_STR,
                section=section,
                msg=(
                    "`cluster-name` is missing. Either add to addon config or pass"
                    " `--cluster-name`"
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
                name=addons_wrong_env,
                product=ADDON_STR,
                section=section,
                msg=f"Wrong OCM environment. Supported envs: {supported_envs}",
                error=True,
            )
            raise click.Abort()


def prepare_addons(addons, ocm_token, endpoint, brew_token, install):
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
        addon["cluster-object"] = Cluster(
            client=ocm_client,
            name=addon_name,
        )

        try:
            addon["cluster-addon"] = ClusterAddOn(
                client=ocm_client, cluster_name=cluster_name, addon_name=addon_name
            )
        except NotFoundException as exc:
            click_echo(
                cluster_name=addon["cluster-name"],
                name=addon_name,
                product=ADDON_STR,
                section="Prepare addon config",
                msg=f"Failed to get addon for cluster {cluster_name} on {exc}.",
                error=True,
            )
            raise click.Abort()

        if install:
            addon["parameters"] = extract_addon_params(addon_dict=addon)

            if addon_name == "managed-odh" and ocm_env == STAGE_STR:
                if brew_token:
                    addon["brew-token"] = brew_token
                else:
                    # TODO: remove to veify?
                    click_echo(
                        cluster_name=addon["cluster-name"],
                        name=addon_name,
                        product=ADDON_STR,
                        section="Prepare addon config",
                        msg="--brew-token flag addon install is missing",
                        error=True,
                    )
                    raise click.Abort()

    return addons


def run_addons_action(addons, install, section, parallel, executor):
    futures = []
    processed_results = []

    for addon in addons:
        addon_obj = addon["cluster-addon"]
        addon_func = addon_obj.install_addon if install else addon_obj.uninstall_addon
        name = addon["name"]
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

        click_echo(
            cluster_name=addon["cluster-name"],
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
