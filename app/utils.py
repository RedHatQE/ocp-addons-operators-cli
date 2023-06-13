import os

import click


def extract_operator_addon_params(resource_and_parameters, resource_type):
    """
    Extract operator or addon parameters from user input

    Args:
        resource_and_parameters (str): user input for resource and parameters
        resource_type (str): operator or addon

    Returns:
        tuple: resource name, dict or list: dict if resource_type == "operator", list if resource_type == "addon"

    Raises:
        click.Abort: if resource_and_parameters is not in the correct format

    Examples:
        >>> extract_operator_addon_params(resource_and_parameters="operator1|param1=value1,param2=value2",
                                          resource_type="operator")
        'operator1', {param1: value1, param2: value2}

        >>> extract_operator_addon_params(resource_and_parameters="addon1|param1=value1,param2=value2",
                                          resource_type="addon")
        addon1, [{'_id': param1, '_value': value1}]

    """
    resource_parameters = [] if resource_type == "addon" else {}
    resource_and_params = resource_and_parameters.split("|")
    resource_name = resource_and_params[0]
    if len(resource_and_params) > 1:
        parameters = resource_and_params[-1].split(",")
        parameters = [_param.strip() for _param in parameters]
        for parameter in parameters:
            if "=" not in parameter:
                click.echo(f"parameters should be id=value, got {parameter}\n")
                raise click.Abort()

            param_name, param_value = parameter.split("=")
            if resource_type == "addon":
                resource_parameters.append({"id": param_name, "value": param_value})
            elif resource_type == "operator":
                resource_parameters[param_name] = param_value
    return resource_name, resource_parameters


def set_debug_os_flags():
    os.environ["OCM_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
    os.environ["OPENSHIFT_PYTHON_WRAPPER_LOG_LEVEL"] = "DEBUG"
