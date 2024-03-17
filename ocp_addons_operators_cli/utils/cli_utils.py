from concurrent.futures import ThreadPoolExecutor, as_completed

import click
from simple_logger.logger import get_logger

from ocp_addons_operators_cli.constants import SUPPORTED_ACTIONS
from ocp_addons_operators_cli.utils.addons_utils import (
    assert_addons_user_input,
    prepare_addons_action,
)
from ocp_addons_operators_cli.utils.general import set_debug_os_flags
from ocp_addons_operators_cli.utils.operators_utils import (
    assert_operators_user_input,
    prepare_operators_action,
)

LOGGER = get_logger(name=__name__)


def abort_no_ocm_token(ocm_token, addons):
    LOGGER.info("Verify OCM TOKEN is not missing from user input")
    if addons and not ocm_token:
        LOGGER.error("`--ocm-token` is required for addon installation")
        raise click.Abort()


def assert_action(action):
    LOGGER.info("Verify `action` from user input")
    if not action:
        LOGGER.error(f"'action' must be provided, supported actions: `{SUPPORTED_ACTIONS}`")
        raise click.Abort()

    if action not in SUPPORTED_ACTIONS:
        LOGGER.error("Provided 'action' is not supported, supported actions: `{SUPPORTED_ACTIONS}`")
        raise click.Abort()


def assert_operators_iib_configuration(kwargs):
    if kwargs.get("operators"):
        LOGGER.info("Verify `iib` configuration for operators installation.")
        s3_bucket_operators_latest_iib_path = kwargs.get("s3_bucket_operators_latest_iib_path")
        if kwargs.get("operators_latest_iib_path") and s3_bucket_operators_latest_iib_path:
            LOGGER.error(
                "Cannot use `s3_bucket_operators_latest_iib_path` and `operators_latest_iib_path` at the same time"
            )
            raise click.Abort()

        if s3_bucket_operators_latest_iib_path:
            if missing_configs := [
                conf
                for conf in ("aws_access_key_id", "aws_region", "aws_secret_access_key")
                if conf not in kwargs or kwargs[conf] is None
            ]:
                LOGGER.error(f"Missing AWS configurations: {missing_configs}")
                raise click.Abort()


def verify_user_input(**kwargs):
    action = kwargs.get("action")
    operators = kwargs.get("operators")
    addons = kwargs.get("addons")
    ocm_token = kwargs.get("ocm_token")
    brew_token = kwargs.get("brew_token")

    abort_no_ocm_token(ocm_token=ocm_token, addons=addons)

    assert_action(action=action)

    if not (operators or addons):
        LOGGER.error("At least one '--operator' or `--addon` option must be provided.")
        raise click.Abort()

    assert_operators_user_input(operators=operators, brew_token=brew_token)
    assert_addons_user_input(addons=addons, brew_token=brew_token)

    assert_operators_iib_configuration(kwargs=kwargs)


def run_install_or_uninstall_products(operators, addons, parallel, debug, install):
    if debug:
        set_debug_os_flags()

    futures = []
    processed_results = []
    action = "install" if install else "uninstall"

    with ThreadPoolExecutor() as executor:
        operators_action_list = prepare_operators_action(
            operators=operators,
            install=install,
        )

        addons_action_list = prepare_addons_action(
            addons=addons,
            install=install,
        )

        LOGGER.info(f"Running products installation; parallel: {parallel}")
        for product_action_tuple in addons_action_list + operators_action_list:
            action_func = product_action_tuple[0]
            action_kwargs = product_action_tuple[1]
            if parallel:
                futures.append(executor.submit(action_func, **action_kwargs))
            else:
                processed_results.append(action_func(**action_kwargs))

    if futures:
        for result in as_completed(futures):
            if result.exception():
                # TODO: Add cluster name, product name and type to threads
                LOGGER.error(
                    f"Failed to {action}: {result.exception()}\n",
                )
                raise click.Abort()
            processed_results.append(result.result())

    addon_names = [addon["name"] for addon in addons]
    operator_names = [operator["name"] for operator in operators]
    LOGGER.info(
        f"Successfully {action} {f'addons: {addon_names}' if addons else ''} "
        f"{f'operators: {operator_names}' if operators else ''}"
    )
    return processed_results


def set_parallel(user_input_parallel, operators, addons):
    LOGGER.info("Setting `parallel` option")
    if len(operators + addons) > 1:
        return user_input_parallel

    return False


def get_iib_config_params(**kwargs):
    return {
        "s3_bucket_operators_latest_iib_path": kwargs.get("s3_bucket_operators_latest_iib_path"),
        "aws_access_key_id": kwargs.get("aws_access_key_id"),
        "aws_region": kwargs.get("aws_region"),
        "aws_secret_access_key": kwargs.get("aws_secret_access_key"),
        "operators_latest_iib_path": kwargs.get("operators_latest_iib_path"),
    }
