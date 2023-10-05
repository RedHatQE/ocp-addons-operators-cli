import click

from ocp_addons_operators_cli.constants import SUPPORTED_ACTIONS
from ocp_addons_operators_cli.utils.general import click_echo

NO_CLUSTER_NO_PRODUCT_FOR_LOG = "All"


def get_operators_from_user_input(**kwargs):
    # From CLI, we get `operator`, from YAML file we get `operators`
    operators = kwargs.get("operator", [])
    if not operators:
        operators = kwargs.get("operators", [])

    for operator in operators:
        if not operator.get("kubeconfig"):
            operator["kubeconfig"] = kwargs.get("kubeconfig")
        operator["brew_token"] = kwargs.get("brew_token")

    return operators


def get_addons_from_user_input(**kwargs):
    # From CLI, we get `addon`, from YAML file we get `addons`
    addons = kwargs.get("addon", [])
    if not addons:
        addons = kwargs.get("addons", [])

    for addon in addons:
        if not addon.get("cluster_name"):
            addon["cluster_name"] = kwargs.get("cluster_name")

    return addons


def abort_no_ocm_token(ocm_token, addons, install, section):
    if not (ocm_token and addons and install):
        click_echo(
            name=NO_CLUSTER_NO_PRODUCT_FOR_LOG,
            product=NO_CLUSTER_NO_PRODUCT_FOR_LOG,
            section=section,
            msg="`--ocm-token` is required for addon installation",
            error=True,
        )
        raise click.Abort()


def assert_operators_user_input(operators, kubeconfig, install, section):
    pass


def assert_addons_user_input(addons, install, section):
    pass


def verify_user_input(**kwargs):
    action = kwargs.get("action")
    operators = kwargs.get("operators")
    addons = kwargs.get("addons")
    kwargs.get("brew_token")
    kubeconfig = kwargs.get("kubeconfig")
    ocm_token = kwargs.get("ocm_token")
    install = kwargs.get("install")

    section = "Verify user input"
    abort_no_ocm_token(
        ocm_token=ocm_token, addons=addons, install=install, section=section
    )

    if not action:
        click_echo(
            name=NO_CLUSTER_NO_PRODUCT_FOR_LOG,
            product=NO_CLUSTER_NO_PRODUCT_FOR_LOG,
            section=section,
            msg=f"'action' must be provided, supported actions: `{SUPPORTED_ACTIONS}`",
            error=True,
        )
        raise click.Abort()

    if action not in SUPPORTED_ACTIONS:
        click_echo(
            name=NO_CLUSTER_NO_PRODUCT_FOR_LOG,
            product=NO_CLUSTER_NO_PRODUCT_FOR_LOG,
            section=section,
            msg=(
                f"'{action}' is not supported, supported actions: `{SUPPORTED_ACTIONS}`"
            ),
            error=True,
        )
        raise click.Abort()

    if not operators or not addons:
        click_echo(
            name=NO_CLUSTER_NO_PRODUCT_FOR_LOG,
            product=NO_CLUSTER_NO_PRODUCT_FOR_LOG,
            section=section,
            msg="At least one '--operator' oe `--addon` option must be provided.",
            error=True,
        )
        raise click.Abort()

    assert_operators_user_input(
        operators=operators, kubeconfig=kubeconfig, install=install, section=section
    )
    assert_addons_user_input(addons=addons, install=install, section=section)
