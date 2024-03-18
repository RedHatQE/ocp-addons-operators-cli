import json
import os
import re
import tempfile

from clouds.aws.session_clients import s3_client


def set_debug_os_flags():
    os.environ["OCM_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
    os.environ["OPENSHIFT_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"


def extract_iibs_from_json(ocp_version, job_name, user_kwargs_dict):
    """
    Extracts operators iibs which are marked as `triggered` by openshift-ci-trigger

    The information can either be saved in an S3 object or in a local file.

    Args:
        ocp_version (str): Openshift version
        job_name (str): openshift ci job name
        user_kwargs_dict (dict): dict with user kwargs

    Returns:
        dict: operator names as keys and iib path as values
    """
    if s3_bucket_operators_latest_iib_path := user_kwargs_dict.get("s3_bucket_operators_latest_iib_path"):
        bucket, key = s3_bucket_operators_latest_iib_path.split("/", 1)
        client = s3_client(region_name=user_kwargs_dict["aws_region"])

        target_file_path = tempfile.NamedTemporaryFile(suffix="operators_latest_iib.json").name

        client.download_file(Bucket=bucket, Key=key, Filename=target_file_path)

    else:
        target_file_path = user_kwargs_dict["local_operators_latest_iib_path"]

    with open(target_file_path) as fd:
        iib_dict = json.load(fd)

    ocp_version_str = f"v{ocp_version}"
    job_dict = iib_dict.get(ocp_version_str, {}).get(job_name, {})
    if not job_dict:
        raise ValueError(f"Missing {ocp_version} / {job_name} in {iib_dict}")

    return {
        operator_name: operator_config["iib"]
        for operator_name, operator_config in job_dict["operators"].items()
        if operator_config["new-iib"]
    }


# TODO: Move to own repository.
def tts(ts):
    """
    Convert time string to seconds.

    Args:
        ts (str): time string to convert, can be and int followed by s/m/h
            if only numbers was sent return int(ts)

    Example:
        >>> tts(ts="1h")
        3600
        >>> tts(ts="3600")
        3600

    Returns:
        int: Time in seconds
    """
    try:
        time_and_unit = re.match(r"(?P<time>\d+)(?P<unit>\w)", str(ts)).groupdict()
    except AttributeError:
        return int(ts)

    _time = int(time_and_unit["time"])
    _unit = time_and_unit["unit"].lower()
    if _unit == "s":
        return _time
    elif _unit == "m":
        return _time * 60
    elif _unit == "h":
        return _time * 60 * 60
    else:
        return int(ts)


def get_iib_dict(user_kwargs_dict):
    s3_bucket_operators_latest_iib_path = user_kwargs_dict.get("s3_bucket_operators_latest_iib_path")
    local_operators_latest_iib_path = user_kwargs_dict.get("local_operators_latest_iib_path")

    ocp_version = os.environ.get("OCP_VERSION")
    job_name = (
        os.environ.get("PARENT_JOB_NAME", os.environ.get("JOB_NAME"))
        if (s3_bucket_operators_latest_iib_path or local_operators_latest_iib_path)
        else None
    )

    if ocp_version and job_name:
        return extract_iibs_from_json(
            ocp_version=ocp_version,
            job_name=job_name,
            user_kwargs_dict=user_kwargs_dict,
        )

    return {}
