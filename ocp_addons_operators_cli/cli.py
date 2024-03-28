import datetime
import os
import sys
import time

import click
from pyaml_env import parse_config
from simple_logger.logger import get_logger

from ocp_addons_operators_cli.click_dict_type import DictParamType
from ocp_addons_operators_cli.constants import INSTALL_STR, SUPPORTED_ACTIONS
from ocp_addons_operators_cli.utils.addons_utils import (
    get_addons_from_user_input,
    prepare_addons,
)
from ocp_addons_operators_cli.utils.cli_utils import (
    run_install_or_uninstall_products,
    set_parallel,
    verify_user_input,
)
from ocp_addons_operators_cli.utils.operators_utils import (
    get_operators_from_user_input,
    prepare_operators,
)

LOGGER = get_logger(name=os.path.split(__file__)[-1])


@click.command("installer")
@click.option(
    "-a",
    "--action",
    type=click.Choice(SUPPORTED_ACTIONS),
    help="Action to perform",
)
@click.option(
    "-o",
    "--operator",
    type=DictParamType(),
    help="""
\b
Operator to install.
Format to pass is:
    'name=operator1;namespace=operator1_namespace; channel=stable;target-namespaces=ns1,ns2;iib=/path/to/iib:123456'
Optional parameters:
    namespace - Operator namespace
    channel - Operator channel to install from, default: 'stable'
    source - Operator source, default: 'redhat-operators'
    target-namespaces - A list of target namespaces for the operator
    source-image - To install operator from specific CatalogSource Image
    iib - To install an operator using custom iib
    """,
    multiple=True,
)
@click.option(
    "-a",
    "--addon",
    type=DictParamType(),
    help="""
\b
Addon to install.
Format to pass is:
    'name=addon1;param1=1;param2=2;rosa=true;timeout=60'
Optional parameters:
    addon parameters - needed parameters for addon installation.
    timeout - addon install / uninstall timeout in seconds, default: 30 minutes.
    rosa - if true, then it will be installed using ROSA cli.
    """,
    multiple=True,
)
@click.option(
    "-e",
    "--endpoint",
    help="SSO endpoint url",
    default="https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token",
    show_default=True,
)
@click.option(
    "-t",
    "--ocm-token",
    help="OCM token (Taken from environment environment `OCM_TOKEN` if not passed)",
    default=os.environ.get("OCM_TOKEN"),
)
@click.option(
    "--brew-token",
    help="""
    \b
    Brew token (needed to install managed-odh addon in stage).
    Default value is taken from environment variable `BREW_TOKEN`, else will be taken from --brew-token flag.
    """,
    default=os.environ.get("BREW_TOKEN"),
)
@click.option("-c", "--cluster-name", help="Cluster name")
@click.option(
    "--kubeconfig",
    help="Path to kubeconfig file",
    type=click.Path(exists=True),
    show_default=True,
)
@click.option(
    "--yaml-config-file",
    help="""
    \b
    YAML file with configuration to install/uninstall addons and operators.
    Any option in YAML file will override the CLI option.
    See manifests/addons-operators.yaml.example for example.
    """,
    type=click.Path(exists=True),
)
@click.option(
    "-p",
    "--parallel",
    help="Run install/uninstall in parallel",
    is_flag=True,
    show_default=True,
)
@click.option(
    "--must-gather-output-dir",
    help="""
\b
Path to must-gather output directory.
must-gather will try to collect data when addon/operator installation fails and cluster can be accessed.
""",
    type=click.Path(exists=True),
)
@click.option("--debug", help="Enable debug logs", is_flag=True)
@click.option(
    "--pdb",
    help="Drop to `ipdb` shell on exception",
    is_flag=True,
    show_default=True,
)
@click.option("--local-operators-latest-iib-path", help="Path to local IIB json file", type=click.Path(exists=True))
@click.option("--s3-bucket-operators-latest-iib-path", help="s3 bucket operators latest iib json path")
@click.option(
    "--aws-access-key-id",
    help="AWS access-key-id, , needed for operators IIB installation when using --s3-bucket-operators-latest-iib-path.",
    default=os.environ.get("AWS_ACCESS_KEY_ID"),
)
@click.option(
    "--aws-secret-access-key",
    help="AWS secret-access-key, needed for operators IIB installation when using --s3-bucket-operators-latest-iib-path.",
    default=os.environ.get("AWS_SECRET_ACCESS_KEY"),
)
@click.option(
    "--aws-region",
    help="AWS region, needed for operators IIB installation when using --s3-bucket-operators-latest-iib-path.",
)
def main(**kwargs):
    LOGGER.info(f"Click Version: {click.__version__}")
    LOGGER.info(f"Python Version: {sys.version}")

    user_kwargs = kwargs
    yaml_config_file = user_kwargs.get("yaml_config_file")
    if yaml_config_file:
        # Update CLI user input from YAML file if exists
        # Since CLI user input has some defaults, YAML file will override them
        user_kwargs.update(parse_config(path=yaml_config_file, default_value=""))

    action = user_kwargs.get("action")
    operators = get_operators_from_user_input(**user_kwargs)
    addons = get_addons_from_user_input(**user_kwargs)
    endpoint = user_kwargs.get("endpoint")
    brew_token = user_kwargs.get("brew_token")
    debug = user_kwargs.get("debug")
    ocm_token = user_kwargs.get("ocm_token")
    parallel = set_parallel(
        user_input_parallel=user_kwargs.get("parallel"),
        operators=operators,
        addons=addons,
    )
    user_kwargs["operators"] = operators
    user_kwargs["addons"] = addons
    install = action == INSTALL_STR
    user_kwargs["install"] = install
    must_gather_output_dir = user_kwargs.get("must_gather_output_dir")

    verify_user_input(**user_kwargs)

    operators = prepare_operators(
        operators=operators,
        install=install,
        user_kwargs_dict=user_kwargs,
    )
    addons = prepare_addons(
        addons=addons,
        ocm_token=ocm_token,
        endpoint=endpoint,
        brew_token=brew_token,
        install=install,
        must_gather_output_dir=must_gather_output_dir,
    )

    run_install_or_uninstall_products(
        operators=operators,
        addons=addons,
        parallel=parallel,
        debug=debug,
        install=install,
    )


if __name__ == "__main__":
    start_time = time.time()
    should_raise = False
    _logger = get_logger(name="main-openshift-cli-installer")
    try:
        main()
    except Exception as ex:
        import traceback

        ipdb = __import__("ipdb")  # Bypass debug-statements pre-commit hook

        if "--pdb" in sys.argv:
            extype, value, tb = sys.exc_info()
            traceback.print_exc()
            ipdb.post_mortem(tb)
        else:
            _logger.error(ex)
            should_raise = True
    finally:
        _logger.info(f"Total execution time: {datetime.timedelta(seconds=time.time() - start_time)}")
        if should_raise:
            sys.exit(1)
