import copy

import pytest


@pytest.fixture()
def _prepare_operators(mocker):
    mocker.patch("ocp_utilities.infra.get_client", return_value="client")
    mocker.patch(
        "ocp_addons_operators_cli.utils.operators_utils.get_cluster_name_from_kubeconfig", return_value="cluster-name"
    )

    # import is done here as mocked functions are used in prepare_operators
    # if the import is done before the mocked functions, the mocked functions are not working
    from ocp_addons_operators_cli.utils.operators_utils import prepare_operators

    return prepare_operators


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
def base_operator_dict():
    return {
        "name": "operator1",
        "namespace": "operator1-ns",
        "timeout": "30m",
        "kubeconfig": "kubeconfig",
        "brew-token": "brew-token",
        "channel": "stable",
        "source": "operators-source",
        "target-namespaces": ["target-namespace"],
    }


@pytest.fixture
def operator_dict_with_iib(base_operator_dict):
    operator_dict = copy.deepcopy(base_operator_dict)
    operator_dict["iib"] = "iib-index-image"
    return operator_dict


def test_prepare_operator_with_iib_from_config(_prepare_operators, operator_dict_with_iib):
    _operators_list = _prepare_operators(operators=[operator_dict_with_iib], install=True, user_kwargs_dict={})
    assert _operators_list[0]["iib_index_image"] == operator_dict_with_iib["iib_index_image"]


def test_prepare_operator_without_iib_from_config(_prepare_operators, base_operator_dict):
    _operators_list = _prepare_operators(operators=[base_operator_dict], install=True, user_kwargs_dict={})
    assert _operators_list[0]["iib_index_image"] is None
