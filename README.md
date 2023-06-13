## ocp-addons-operators-cli
CLI to Install/Uninstall Addons/operators on OCM/OCP clusters.

### Container
image locate at [ocp-addons-operators-cli](https://quay.io/repository/redhat_msi/ocp-addons-operators-cli)  
To pull the image: `podman pull quay.io/redhat_msi/ocp-addons-operators-cli`

### Usages

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli addon --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli addon install --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli addon uninstall --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli operator --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli operator install --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli operator uninstall --help
```

### Local run

clone the [repository](https://github.com/RedHatQE/ocp-addons-operators-cli.git)

```
git clone https://github.com/RedHatQE/ocp-addons-operators-cli.git
```

Install [poetry](https://github.com/python-poetry/poetry)

Use `poetry run app/cli.py` to execute the cli.

```
poetry install
poetry run python app/cli.py --help
```


### Addons

Each command can be run via container `podman run quay.io/redhat_msi/ocp-addons-operators-cli` or via poetry command `poetry run app/cli.py`

#### Install Addon
##### One addon

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addon \
    -t $OCM_TOKEN \
    -a ocm-addon-test-operator|has-external-resources=false,aws-cluster-test-param=false \
    -c cluster-name \
    install
```

##### Multiple addons

To run multiple addons install in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addon \
    -t $OCM_TOKEN \
    -a ocm-addon-test-operator|has-external-resources=false,aws-cluster-test-param=false \
    -a ocm-addon-test-operator-2|has-external-resources=false,aws-cluster-test-param=false \
    -c cluster-name \
    install
```

#### Uninstall Addon
##### One addon

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addon \
    -t $OCM_TOKEN \
    -a ocm-addon-test-operator \
    -c cluster-name \
    uninstall
```

##### Multiple addons

To run multiple addons uninstall in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addon \
    -t $OCM_TOKEN \
    -a ocm-addon-test-operator \
    -a ocm-addon-test-operator-2 \
    -c cluster-name \
    uninstall
```

#### ROSA cli
Use --rosa addon_name to specify which addon to install/uninstall with ROSA cli.
Specify addons with addon names, separated by a comma.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addon \
    -t $OCM_TOKEN \
    -a ocm-addon-test-operator-1 \
    -a ocm-addon-test-operator-2 \
    -a ocm-addon-test-operator-3 \
    -c cluster-name \
    --rosa ocm-addon-test-operator-1,ocm-addon-test-operator-3 \
    install
```
Only addons `ocm-addon-test-operator-1` and `ocm-addon-test-operator-3` will be installed with ROSA cli.

### Operators
#### Install Operator
##### One operator

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    operator \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'rhods-operator|namespace=redhat-ods-operator' \
    install
```

##### Multiple operator

To run multiple operators install in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    operator \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'rhods-operator|namespace=redhat-ods-operator' \
    -o 'servicemeshoperator' \
    install
```

#### Uninstall Operator
##### One operator

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    operator \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'rhods-operator|namespace=redhat-ods-operator' \
    uninstall
```

##### Multiple operator

To run multiple operators uninstall in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    operator \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'rhods-operator|namespace=redhat-ods-operator' \
    -o 'servicemeshoperator' \
    uninstall
```
