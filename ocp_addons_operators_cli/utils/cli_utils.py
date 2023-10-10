from concurrent.futures import ThreadPoolExecutor, as_completed

import click
from simple_logger.logger import get_logger

from ocp_addons_operators_cli.constants import ERROR_LOG_COLOR, SUPPORTED_ACTIONS
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
    if addons and not ocm_token:
        LOGGER.error("`--ocm-token` is required for addon installation")
        raise click.Abort()


def verify_user_input(**kwargs):
    action = kwargs.get("action")
    operators = kwargs.get("operators")
    addons = kwargs.get("addons")
    ocm_token = kwargs.get("ocm_token")

    abort_no_ocm_token(ocm_token=ocm_token, addons=addons)

    if not action:
        LOGGER.error(
            f"'action' must be provided, supported actions: `{SUPPORTED_ACTIONS}`"
        )
        raise click.Abort()

    if not (operators or addons):
        LOGGER.error("At least one '--operator' or `--addon` option must be provided.")
        raise click.Abort()

    assert_operators_user_input(operators=operators)
    assert_addons_user_input(addons=addons, brew_token=kwargs.get("brew_token"))


def run_install_or_uninstall_products(operators, addons, parallel, debug, install):
    if debug:
        set_debug_os_flags()

    futures = []
    processed_results = []

    with ThreadPoolExecutor() as executor:
        operators_action_list = prepare_operators_action(
            operators=operators,
            install=install,
        )

        addons_action_list = prepare_addons_action(
            addons=addons,
            install=install,
        )

        for product_action_tuple in addons_action_list + operators_action_list:
            action_func = product_action_tuple[0]
            action_kwargs = product_action_tuple[1]
            if parallel:
                futures.append(executor.submit(action_func(), **action_kwargs))
            else:
                processed_results.append(action_func(**action_kwargs))

    if futures:
        for result in as_completed(futures):
            if result.exception():
                # TODO: Add cluster name, product name and type to threads
                click.secho(
                    f"Failed to {'install' if install else 'uninstall'}:"
                    f" {result.exception()}\n",
                    fg=ERROR_LOG_COLOR,
                )
                raise click.Abort()
            processed_results.append(result.result())

    return processed_results


def set_parallel(user_input_parallel, operators, addons):
    if len(operators + addons) > 1:
        return user_input_parallel

    return False
