from concurrent.futures import ThreadPoolExecutor, as_completed

import click

from ocp_addons_operators_cli.constants import (
    ADDON_STR,
    ERROR_LOG_COLOR,
    SUPPORTED_ACTIONS,
)
from ocp_addons_operators_cli.utils.addons_utils import (
    assert_addons_user_input,
    run_addons_action,
)
from ocp_addons_operators_cli.utils.general import click_echo, set_debug_os_flags
from ocp_addons_operators_cli.utils.operators_utils import (
    assert_operators_user_input,
    run_operator_action,
)

NO_PRODUCT_NAME_FOR_LOG = "All"


def abort_no_ocm_token(ocm_token, addons, section):
    if addons and not ocm_token:
        click_echo(
            product=ADDON_STR,
            section=section,
            msg="`--ocm-token` is required for addon installation",
            error=True,
        )
        raise click.Abort()


def verify_user_input(**kwargs):
    action = kwargs.get("action")
    operators = kwargs.get("operators")
    addons = kwargs.get("addons")
    ocm_token = kwargs.get("ocm_token")

    section = "Verify user input"
    abort_no_ocm_token(ocm_token=ocm_token, addons=addons, section=section)

    if not action:
        click_echo(
            section=section,
            msg=f"'action' must be provided, supported actions: `{SUPPORTED_ACTIONS}`",
            error=True,
        )
        raise click.Abort()

    if not (operators or addons):
        click_echo(
            section=section,
            msg="At least one '--operator' oe `--addon` option must be provided.",
            error=True,
        )
        raise click.Abort()

    assert_operators_user_input(operators=operators, section=section)
    assert_addons_user_input(addons=addons, section=section)


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
                # TODO: Add cluster name, product name and type to threads
                click.secho(
                    f"Failed to {'install' if install else 'uninstall'}:"
                    f" {result.exception()}\n",
                    fg=ERROR_LOG_COLOR,
                )
                raise click.Abort()


def set_parallel(user_input_parallel, operators, addons):
    if (operators and len(operators)) == 1 or (addons and len(addons)) == 1:
        return False

    return user_input_parallel
