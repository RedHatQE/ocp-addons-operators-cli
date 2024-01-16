import os


def main():
    addons = ""
    operators = ""

    cmd = "poetry run python ocp_addons_operators_cli/cli.py"
    os_env = os.environ
    if action := os_env.get("ACTION"):
        cmd += f" --action={action}"
    if config_file := os_env.get("ADDONS_OPERATORS_YAML_CONFIG_FILE"):
        cmd += f" --yaml-config-file={config_file}"
    if cluster_name := os_env.get("CLUSTER_NAME"):
        cmd += f" --cluster-name={cluster_name}"
    if os_env.get("PARALLEL") == "true":
        cmd += " --parallel"
    if ocm_token := os_env.get("OCM_TOKEN"):
        cmd += f" --ocm-token={ocm_token}"
    if brew_token := os_env.get("BREW_TOKEN"):
        cmd += f" --brew-token={brew_token}"
    if must_gather := os_env.get("MUST_GATHER_OUTPUT_DIR"):
        cmd += f" --must-gather-output-dir={must_gather}"
    if endpoint := os_env.get("ENDPOINT"):
        cmd += f" --endpoint={endpoint}"
    if kubeconfig := os_env.get("KUBECONFIG"):
        cmd += f" --kubeconfig={kubeconfig}"

    if addon1 := os_env.get("ADDON1"):
        addons += f" --addon='{addon1}'"
    if addon2 := os_env.get("ADDON2"):
        addons += f" --addon='{addon2}'"
    if addon3 := os_env.get("ADDON3"):
        addons += f" --addon='{addon3}'"
    if addon4 := os_env.get("ADDON4"):
        addons += f" --addon='{addon4}'"
    if addon5 := os_env.get("ADDON5"):
        addons += f" --addon='{addon5}'"

    if operator1 := os_env.get("OPERATOR1"):
        operators += f" --operator='{operator1}'"
    if operator2 := os_env.get("OPERATOR2"):
        operators += f" --operator='{operator2}'"
    if operator3 := os_env.get("OPERATOR3"):
        operators += f" --operator='{operator3}'"
    if operator4 := os_env.get("OPERATOR4"):
        operators += f" --operator='{operator4}'"
    if operator5 := os_env.get("OPERATOR5"):
        operators += f" --operator='{operator5}'"

    cmd += f" {operators} {addons}"

    print(cmd)


if __name__ == "__main__":
    main()
