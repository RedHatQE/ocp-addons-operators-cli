def extract_addon_params(addon_dict):
    """
    Extract addon parameters from user input

    Args:
        addon_dict (dict): dict constructed from addon user input

    Returns:
        list: list of addon parameters dicts

    """
    exclude_list = [
        "cluster-addon",
        "name",
        "timeout",
        "rosa",
        "ocm-client",
        "cluster-object",
        "ocm-env",
        "brew-token",
        "cluster-name",
    ]
    resource_parameters = []

    for key, value in addon_dict.items():
        if key in exclude_list:
            continue

        resource_parameters.append({"id": key, "value": value})

    return resource_parameters
