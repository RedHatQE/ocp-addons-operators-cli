import copy
import os

import pytest
from semver import Version

from ocp_addons_operators_cli.utils.operators_utils import prepare_operators


pytestmark = pytest.mark.usefixtures("mocked_prepare_operators")


@pytest.fixture
def mocked_prepare_operators(request, mocker, base_iib_dict):
    operators_utils_path = "ocp_addons_operators_cli.utils.operators_utils"

    mocker.patch(
        f"{operators_utils_path}.get_client",
        return_value="client",
    )
    mocker.patch(
        f"{operators_utils_path}.get_cluster_name_from_kubeconfig",
        return_value="cluster-name",
    )

    if hasattr(request, "param") and request.param.get("iib_json"):
        mocker.patch(
            f"{operators_utils_path}.get_cluster_version",
            return_value=request.param["cluster_version"],
        )

        mocker.patch(
            f"{operators_utils_path}.get_operators_iibs_config_from_json",
            return_value=base_iib_dict,
        )


@pytest.fixture
def base_iib_dict(request):
    return {
        "v4.15": {
            "4_15_job": {
                "operators": {
                    "operator-1": {
                        "new-iib": request.param,
                        "iib": "operator-1-iib",
                    },
                },
                "ci": "jenkins",
            }
        },
    }


@pytest.fixture
def base_operator_dict():
    return {
        "name": "operator-1",
        "namespace": "operator-1-ns",
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


@pytest.fixture
def operator_dict_with_unmatched_operator(base_operator_dict):
    operator_dict = copy.deepcopy(base_operator_dict)
    operator_dict["name"] = "operator-2"
    return operator_dict


@pytest.fixture
def job_name_as_environment_variable():
    job_name = "4_15_job"
    os.environ["PARENT_JOB_NAME"] = job_name
    yield job_name


@pytest.fixture
def prepare_operator_user_kwargs_with_local_iib_path():
    return {"local_operators_latest_iib_path": "iib_path"}


def cluster_version_major_minor_str(cluster_version):
    return f"v{cluster_version.major}.{cluster_version.minor}"


@pytest.mark.parametrize(
    "mocked_prepare_operators",
    [{"iib_json": True, "cluster_version": Version.parse("4.15.0")}],
    indirect=True,
)
class TestPrepareOperatorFromJson:
    @pytest.mark.parametrize("base_iib_dict", [True], indirect=True)
    def test_prepare_operator_with_new_iib_from_json(
        self,
        request,
        base_iib_dict,
        base_operator_dict,
        job_name_as_environment_variable,
        prepare_operator_user_kwargs_with_local_iib_path,
    ):
        _operators_list = prepare_operators(
            operators=[base_operator_dict],
            install=True,
            user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
        )

        operator_name = _operators_list[0]["name"]
        operator_iib = base_iib_dict[
            cluster_version_major_minor_str(
                cluster_version=request.node.callspec.params["mocked_prepare_operators"]["cluster_version"]
            )
        ][job_name_as_environment_variable]["operators"][operator_name]["iib"]

        assert operator_iib == _operators_list[0]["iib_index_image"]

    @pytest.mark.parametrize("base_iib_dict", [True], indirect=True)
    def test_prepare_operator_with_new_iib_from_json_no_operator_match(
        self,
        base_iib_dict,
        operator_dict_with_unmatched_operator,
        job_name_as_environment_variable,
        prepare_operator_user_kwargs_with_local_iib_path,
    ):
        _operators_list = prepare_operators(
            operators=[operator_dict_with_unmatched_operator],
            install=True,
            user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
        )
        assert _operators_list[0]["iib_index_image"] is None

    @pytest.mark.parametrize("base_iib_dict", [False], indirect=True)
    def test_prepare_operator_with_no_new_iib_from_json(
        self,
        base_iib_dict,
        base_operator_dict,
        job_name_as_environment_variable,
        prepare_operator_user_kwargs_with_local_iib_path,
    ):
        _operators_list = prepare_operators(
            operators=[base_operator_dict],
            install=True,
            user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
        )

        assert _operators_list[0]["iib_index_image"] is None

    @pytest.mark.parametrize("base_iib_dict", [True], indirect=True)
    def test_prepare_operator_with_iib_from_json_no_job_match(
        self,
        request,
        base_iib_dict,
        base_operator_dict,
        prepare_operator_user_kwargs_with_local_iib_path,
    ):
        missing_job_name = "4_16_job"
        os.environ["PARENT_JOB_NAME"] = missing_job_name
        cluster_version_major_minor = cluster_version_major_minor_str(
            cluster_version=request.node.callspec.params["mocked_prepare_operators"]["cluster_version"]
        )
        with pytest.raises(
            ValueError,
            match=f".*Missing {cluster_version_major_minor} / {missing_job_name}.*",
        ):
            prepare_operators(
                operators=[base_operator_dict],
                install=True,
                user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
            )


@pytest.mark.parametrize(
    "mocked_prepare_operators, base_iib_dict",
    [
        pytest.param(
            {"iib_json": True, "cluster_version": Version.parse("1.2.3")},
            True,
        ),
    ],
    indirect=True,
)
def test_prepare_operator_with_iib_from_json_no_ocp_match(
    request,
    base_iib_dict,
    base_operator_dict,
    job_name_as_environment_variable,
    prepare_operator_user_kwargs_with_local_iib_path,
):
    cluster_version_major_minor = cluster_version_major_minor_str(
        cluster_version=request.node.callspec.params["mocked_prepare_operators"]["cluster_version"]
    )
    with pytest.raises(
        ValueError,
        match=f".*Missing {cluster_version_major_minor} / {job_name_as_environment_variable}.*",
    ):
        prepare_operators(
            operators=[base_operator_dict],
            install=True,
            user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
        )


@pytest.mark.parametrize("base_iib_dict", [True], indirect=True)
class TestPrepareOperatorFromConfig:
    def test_prepare_operator_with_iib_from_config(self, operator_dict_with_iib):
        _operators_list = prepare_operators(operators=[operator_dict_with_iib], install=True, user_kwargs_dict={})
        assert _operators_list[0]["iib_index_image"] == operator_dict_with_iib["iib_index_image"]

    def test_prepare_operator_without_iib_from_config(self, base_operator_dict):
        _operators_list = prepare_operators(operators=[base_operator_dict], install=True, user_kwargs_dict={})
        assert _operators_list[0]["iib_index_image"] is None
