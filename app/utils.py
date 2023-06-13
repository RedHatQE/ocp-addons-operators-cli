import os


def extract_addon_params(addon_dict):
    """
    Extract addon parameters from user input

    Args:
        addon_dict (dict): dict constructed from addon user input

    Returns:
        list: list of addon parameters dicts

    """
    exclude_list = ["name", "timeout", "rosa"]
    resource_parameters = []

    for key, value in addon_dict.items():
        if key not in exclude_list:
            resource_parameters.append({"id": key, "value": value})

    return resource_parameters


def set_debug_os_flags():
    os.environ["OCM_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
    os.environ["OPENSHIFT_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
