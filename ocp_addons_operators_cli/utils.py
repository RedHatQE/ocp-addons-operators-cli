import json
import os

import requests


def set_debug_os_flags():
    os.environ["OCM_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
    os.environ["OPENSHIFT_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"


def extract_iibs_from_json(ocp_version, job_name):
    """
    Extracts operators iibs which are marked as `triggered` by openshift-ci-trigger

    Use https://raw.githubusercontent.com/RedHatQE/openshift-ci-trigger/main/operators-latest-iib.json
    to extract iib data.

    Args:
        ocp_version (str): Openshift version
        job_name (str): openshift ci job name

    Returns:
        dict: operator names as keys and iib path as values
    """
    iib_dict = json.loads(
        requests.get(
            "https://raw.githubusercontent.com/RedHatQE/openshift-ci-trigger/main/operators-latest-iib.json"
        ).text
    )
    ocp_version_str = f"v{ocp_version}"
    job_dict = iib_dict.get(ocp_version_str, {}).get(job_name, {})
    if not job_dict:
        raise ValueError(f"Missing {ocp_version} / {job_name} in {iib_dict}")
    return {
        operator_name: operator_config["iib"]
        for operator_name, operator_config in iib_dict[ocp_version_str][
            job_name
        ].items()
        if operator_config["triggered"]
    }
