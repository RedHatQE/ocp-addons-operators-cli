import pytest

from ocp_addons_operators_cli.utils.operators_utils import prepare_operators


@pytest.fixture
def iib_dict():
    return {
        {
            "v4.15": {
                "4_15_job": {
                    "operators": {
                        "operator-1": {
                            "new-iib": True,
                            "iib": "operator-1-iib",
                        },
                        "operator-2": {
                            "new-iib": False,
                            "iib": "operator-2-iib",
                        },
                        "operator-3": {
                            "new-iib": True,
                        },
                    },
                    "ci": "jenkins",
                }
            },
        }
    }


@pytest.fixture
def operators_list():
    return [
        {
            "name": "operator1",
            "namespace": "operator1-ns",
            "iib": "operator1-iib",
            "timeout": "30m",
            "kubeconfig": "kubeconfig",
            "brew-token": "brew-token",
            "channel": "stable",
            "source": "operators-source",
            "target-namespaces": ["target-namespace"],
        }
    ]


def test_prepare_operator_with_iib_from_config(
    mocker,
    operators_list,
):
    mocker.patch("ocp_utilities.infra.get_client", return_value="client")
    # mocker.patch(
    #     "ocp_addons_operators_cli.utils.general.get_operators_iibs_config_from_json",
    #     return_value=None,
    # )
    # import ipdb
    #
    # ipdb.set_trace()
    prepare_operators(operators=operators_list, install=True, user_kwargs_dict={})
