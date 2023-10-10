## ocp-addons-operators-cli
CLI to Install/Uninstall Addons/operators on OCM/OCP clusters.

### Container
image locate at [ocp-addons-operators-cli](https://quay.io/repository/redhat_msi/ocp-addons-operators-cli)  
To pull the image: `podman pull quay.io/redhat_msi/ocp-addons-operators-cli`

### Local run

clone the [repository](https://github.com/RedHatQE/ocp-addons-operators-cli.git)

```
git clone https://github.com/RedHatQE/ocp-addons-operators-cli.git
```

Install [poetry](https://github.com/python-poetry/poetry)

Use `poetry run python ocp_addons_operators_cli/cli.py` to execute the cli.

```
poetry install
poetry run python ocp_addons_operators_cli/cli.py --help
```

### Usages
#### Install/uninstall addons and/or operators from YAML file
User can install/uninstall addons and/or operators by sending YAML file instead with CLI args
Example YAML file can be found [here](ocp_addons_operators_cli/manifests/addons-operators.yaml.example)
pass `--yaml-config-file=.local/addons-operators.yaml` to use YAML file.
Action also can be passed to the CLI as `--action install/uninstall` instead of specifying the action in the YAML file.
`poetry run python ocp_addons_operators_cli/cli.py --action install --yaml-config-file addons-operators.yaml`

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli --help
```

### Global CLI configuration
* `--action`: install/uninstall product(s)
* `--brew-token`: Brew token (needed to install managed-odh addon in stage). Default value is taken from environment variable `BREW_TOKEN`.
* `--debug`: Enable debug logs
* `--parallel`: Run install/uninstall in parallel

* Operators configuration
  * `--kubeconfig`: Path to kubeconfig; can be overwritten by cluster-specific configuration
* Addons configuration
  * `--endpoint`: SSO endpoint url, defaults to https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token
  * `--ocm-token`: OCM token, defaults to `OCM_TOKEN` environment variable
  * `--cluster-name`: Addon's cluster name; can be overwritten by cluster-specific configuration

### Addon/Operator user args

Each `--addon` or `operator` accept args, the format is `arg=value;`
###### Common args:
* `name=name`: Name of the operator/addon to install/uninstall
* `timeout=300`: timeout to wait for the operator/addon to be installed/uninstalled; format examples: `1h`, `30m`, `3600s`

###### Addon args:
* `rosa=true`: Use rosa cli to install/uninstall the addon
* `cluster-name=cluster`: Addon's cluster name; if not provided, global configuration will be used

###### Operator args:
* `iib=/path/to/iib:123456`: Install the operator using the provided IIB
* `channel=stable`: Operator channel to install from, default: 'stable'
* `source=redhat-operators`: Operator source, default: 'redhat-operators'
* `kubeconfig`: Path to kubeconfig; if not provided, global configuration will be used


#### Install Addon
##### One addon

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator;has-external-resources=false;aws-cluster-test-param=false;timeout=600' \
    -c cluster-name
```

##### Multiple addons

To run multiple addons install in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator;has-external-resources=false;aws-cluster-test-param=false;timeout=600' \
    -a 'name=ocm-addon-test-operator-2;has-external-resources=false;aws-cluster-test-param=false;timeout=600' \
    -c cluster-name
```

#### Uninstall Addon
##### One addon

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action uninstall \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator' \
    -c cluster-name
```

##### Multiple addons

To run multiple addons uninstall in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator' \
    -a 'name=ocm-addon-test-operator-2' \
    -c cluster-name
```

##### Multiple addons on multiple clusters

To run multiple addons uninstall in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator;cluster-name=cluster1' \
    -a 'name=ocm-addon-test-operator-2;cluster-name=cluster2'
```

#### ROSA cli
Pass 'rosa=true' in the addon `-a` arg.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator;has-external-resources=false;aws-cluster-test-param=false;rosa=true;timeout=600'
    -c cluster-name
```
Only addons `ocm-addon-test-operator-1` and `ocm-addon-test-operator-3` will be installed with ROSA cli.

### Operators
#### Install Operator
##### One operator

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'name=rhods-operator;namespace=redhat-ods-operator'
```

##### Multiple operator

To run multiple operators install in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'name=rhods-operator;namespace=redhat-ods-operator;timeout=600' \
    -o 'name=servicemeshoperator'
```

##### Multiple operator on multiple clusters

To run multiple operators install in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    -o 'name=rhods-operator;namespace=redhat-ods-operator;timeout=600;kubeconfig=/tmp/kubeconfig1' \
    -o 'name=servicemeshoperator;kubeconfig=/tmp/kubeconfig2'
```

##### Install operator using IIB (ndex-image)

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    --brew-token token \
    -o 'name=rhods-operator;namespace=redhat-ods-operator;iib=/path/to/iib:123456'
```

#### Uninstall Operator
##### One operator

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action uninstall \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'name=servicemeshoperator'
```

##### Multiple operator

To run multiple operators uninstall in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action uninstall \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'name=rhods-operator;namespace=redhat-ods-operator' \
    -o 'name=servicemeshoperator;timeout=600'
```


##### Operator and addon

To run multiple operators install in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    --action install \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -t $OCM_TOKEN \
    -c cluster1 \
    -a 'name=ocm-addon-test-operator;has-external-resources=false;aws-cluster-test-param=false' \
    -o 'name=servicemeshoperator;timeout=600'
```
