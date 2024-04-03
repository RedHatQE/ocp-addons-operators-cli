import json
import os
import re
import tempfile

from clouds.aws.session_clients import s3_client
from simple_logger.logger import get_logger


LOGGER = get_logger(name=__name__)


def set_debug_os_flags():
    os.environ["OCM_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
    os.environ["OPENSHIFT_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"


def get_operators_iibs_config_from_json(
    s3_bucket_operators_latest_iib_path=None,
    aws_region=None,
    local_operators_latest_iib_path=None,
):
    """
    Get operators iibs data from an S3 object or in a local file.

    Args:
        s3_bucket_operators_latest_iib_path (str, optional): full path to S3 object containing IIB data
        aws_region (str, optional): AWS region
        local_operators_latest_iib_path (str, optional): full path to local file containing IIB data

    Returns:
        dict: operators iibs data
    """
    if s3_bucket_operators_latest_iib_path:
        bucket, key = s3_bucket_operators_latest_iib_path.split("/", 1)
        client = s3_client(region_name=aws_region)

        target_file_path = tempfile.NamedTemporaryFile(suffix="operators_latest_iib.json").name

        LOGGER.info(f"Downloading {key} from {bucket} to {target_file_path}")
        client.download_file(Bucket=bucket, Key=key, Filename=target_file_path)

    else:
        target_file_path = local_operators_latest_iib_path

    with open(target_file_path) as fd:
        return json.load(fd)


def get_operator_iib(iib_dict, ocp_version, job_name, operator_name):
    ocp_version_str = f"v{ocp_version}"
    job_dict = iib_dict.get(ocp_version_str, {}).get(job_name, {})

    if not job_dict:
        raise ValueError(f"Missing {ocp_version_str} / {job_name} in {iib_dict}")

    if (operator_dict := job_dict["operators"].get(operator_name)) and operator_dict.get("new-iib"):
        operator_iib = operator_dict.get("iib")
        LOGGER.info(f"Extracted operator `{operator_name}` iib: {operator_iib}")
        return operator_iib

    return None


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
