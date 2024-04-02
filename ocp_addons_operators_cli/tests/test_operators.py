import copy
import os

import pytest
from semver import Version


@pytest.fixture
def cluster_version(request):
    if request.param:
        return Version.parse(request.param)


@pytest.fixture
def cluster_version_major_minor(cluster_version):
    return f"v{cluster_version.major}.{cluster_version.minor}"


@pytest.fixture
def _prepare_operators(request, mocker, cluster_version, base_iib_dict):
    mocker.patch("ocp_utilities.infra.get_client", return_value="client")

    if request.param.get("iib_json"):
        mocker.patch(
            "ocp_utilities.cluster_versions.get_cluster_version",
            return_value=cluster_version,
        )

        mocker.patch(
            "ocp_addons_operators_cli.utils.operators_utils.get_operators_iibs_config_from_json",
            return_value=base_iib_dict,
        )

    mocker.patch(
        "ocp_addons_operators_cli.utils.operators_utils.get_cluster_name_from_kubeconfig",
        return_value="cluster-name",
    )

    # import is done here as mocked functions are used in prepare_operators
    # if the import is done before the mocked functions, the mocked functions are not working
    # the order of mocked functions is important; place first the ones that are later imported in the other mocked functions
    from ocp_addons_operators_cli.utils import operators_utils

    yield operators_utils.prepare_operators

    mocker.stopall()


@pytest.fixture
def base_iib_dict(request):
    if request.param:
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


@pytest.mark.parametrize("_prepare_operators", [{"iib_json": True}], indirect=True)
class TestPrepareOperatorsFromIIB:
    @pytest.mark.parametrize(
        "cluster_version, base_iib_dict",
        [
            pytest.param(
                "4.15.0",
                True,
            ),
        ],
        indirect=True,
    )
    def test_prepare_operator_with_new_iib_from_json(
        self,
        cluster_version,
        cluster_version_major_minor,
        base_iib_dict,
        _prepare_operators,
        base_operator_dict,
        job_name_as_environment_variable,
        prepare_operator_user_kwargs_with_local_iib_path,
    ):
        _operators_list = _prepare_operators(
            operators=[base_operator_dict],
            install=True,
            user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
        )

        operator_name = _operators_list[0]["name"]
        operator_iib = base_iib_dict[cluster_version_major_minor][job_name_as_environment_variable]["operators"][
            operator_name
        ]["iib"]

        assert operator_iib == _operators_list[0]["iib_index_image"]

    @pytest.mark.parametrize(
        "cluster_version, base_iib_dict",
        [
            pytest.param(
                "4.15.0",
                True,
            ),
        ],
        indirect=True,
    )
    def test_prepare_operator_with_new_iib_from_json_no_operator_match(
        self,
        cluster_version,
        cluster_version_major_minor,
        base_iib_dict,
        _prepare_operators,
        operator_dict_with_unmatched_operator,
        job_name_as_environment_variable,
        prepare_operator_user_kwargs_with_local_iib_path,
    ):
        _operators_list = _prepare_operators(
            operators=[operator_dict_with_unmatched_operator],
            install=True,
            user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
        )
        assert _operators_list[0]["iib_index_image"] is None

    @pytest.mark.parametrize(
        "cluster_version, base_iib_dict",
        [
            pytest.param(
                "4.15.0",
                False,
            ),
        ],
        indirect=True,
    )
    def test_prepare_operator_with_no_new_iib_from_json(
        self,
        cluster_version,
        cluster_version_major_minor,
        base_iib_dict,
        _prepare_operators,
        base_operator_dict,
        job_name_as_environment_variable,
        prepare_operator_user_kwargs_with_local_iib_path,
    ):
        _operators_list = _prepare_operators(
            operators=[base_operator_dict],
            install=True,
            user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
        )

        assert _operators_list[0]["iib_index_image"] is None

    @pytest.mark.parametrize(
        "cluster_version, base_iib_dict",
        [
            pytest.param(
                "9.9.9",
                True,
            ),
        ],
        indirect=True,
    )
    def test_prepare_operator_with_iib_from_json_no_ocp_match(
        self,
        cluster_version,
        cluster_version_major_minor,
        base_iib_dict,
        _prepare_operators,
        base_operator_dict,
        job_name_as_environment_variable,
        prepare_operator_user_kwargs_with_local_iib_path,
    ):
        with pytest.raises(
            ValueError,
            match=f".*Missing {cluster_version_major_minor} / {job_name_as_environment_variable}.*",
        ):
            from ocp_utilities.cluster_versions import get_cluster_version

            get_cluster_version()

            _prepare_operators(
                operators=[base_operator_dict],
                install=True,
                user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
            )

    @pytest.mark.parametrize(
        "cluster_version, base_iib_dict",
        [
            pytest.param(
                "4.15.0",
                True,
            ),
        ],
        indirect=True,
    )
    def test_prepare_operator_with_iib_from_json_no_job_match(
        self,
        cluster_version,
        cluster_version_major_minor,
        base_iib_dict,
        _prepare_operators,
        base_operator_dict,
        prepare_operator_user_kwargs_with_local_iib_path,
    ):
        missing_job_name = "4_16_job"
        os.environ["PARENT_JOB_NAME"] = missing_job_name
        with pytest.raises(
            ValueError,
            match=f".*Missing {cluster_version_major_minor} / {missing_job_name}.*",
        ):
            _prepare_operators(
                operators=[base_operator_dict],
                install=True,
                user_kwargs_dict=prepare_operator_user_kwargs_with_local_iib_path,
            )


def test_prepare_operator_with_iib_from_config(_prepare_operators, operator_dict_with_iib):
    _operators_list = _prepare_operators(operators=[operator_dict_with_iib], install=True, user_kwargs_dict={})
    assert _operators_list[0]["iib_index_image"] == operator_dict_with_iib["iib_index_image"]


def test_prepare_operator_without_iib_from_config(_prepare_operators, base_operator_dict):
    _operators_list = _prepare_operators(operators=[base_operator_dict], install=True, user_kwargs_dict={})
    assert _operators_list[0]["iib_index_image"] is None
