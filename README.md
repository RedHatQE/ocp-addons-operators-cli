## ocp-addons-operators-cli
CLI to Install/Uninstall Addons/operators on OCM/OCP clusters.

### Container
image locate at [ocp-addons-operators-cli](https://quay.io/repository/redhat_msi/ocp-addons-operators-cli)  
To pull the image: `podman pull quay.io/redhat_msi/ocp-addons-operators-cli`

### Usages

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli addons --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli addons install --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli addons uninstall --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli operators --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli operators install --help
podman run quay.io/redhat_msi/ocp-addons-operators-cli operators uninstall --help
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

### Addon/Operator user args

Each `--addon` or `operator` accept args, the format is `arg=value;`
###### Common args:
* `name=name`: Name of the operator/addon to install/uninstall
* `timeout=300`: timeout in seconds to wait for the operator/addon to be installed/uninstalled

###### Addon args:
* `rosa=true`: Use rosa cli to install/uninstall the addon

###### Operator args:
* `iib=/path/to/iib:123456`: Install the operator using the provided IIB
* `channel=stable`: Operator channel to install from, default: 'stable'
* `source=redhat-operators`: Operator source, default: 'redhat-operators'


#### Install Addon
##### One addon

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addons \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator;has-external-resources=false;aws-cluster-test-param=false;timeout=600' \
    -c cluster-name \
    install
```

##### Multiple addons

To run multiple addons install in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addons \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator;has-external-resources=false;aws-cluster-test-param=false;timeout=600' \
    -a 'name=ocm-addon-test-operator-2;has-external-resources=false;aws-cluster-test-param=false;timeout=600' \
    -c cluster-name \
    install
```

#### Uninstall Addon
##### One addon

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addons \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator' \
    -c cluster-name \
    uninstall
```

##### Multiple addons

To run multiple addons uninstall in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addons \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator' \
    -a 'name=ocm-addon-test-operator-2' \
    -c cluster-name \
    uninstall
```

#### ROSA cli
Pass 'rosa=true' in the addon `-a` arg.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    addon \
    -t $OCM_TOKEN \
    -a 'name=ocm-addon-test-operator;has-external-resources=false;aws-cluster-test-param=false;rosa=true;timeout=600'
    -c cluster-name \
    install
```
Only addons `ocm-addon-test-operator-1` and `ocm-addon-test-operator-3` will be installed with ROSA cli.

### Operators
#### Install Operator
##### One operator

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    operators \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'name=rhods-operator;namespace=redhat-ods-operator' \
    install
```

##### Multiple operator

To run multiple operators install in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    operators \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'name=rhods-operator;namespace=redhat-ods-operator;timeout=600' \
    -o 'name=servicemeshoperator' \
    install
```

##### Install operator using IIB (ndex-image)

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    operators \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    --brew-token token \
    -o 'name=rhods-operator;namespace=redhat-ods-operator;iib=/path/to/iib:123456' \
    install
```

#### Uninstall Operator
##### One operator

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    operators \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'name=servicemeshoperator'
    uninstall
```

##### Multiple operator

To run multiple operators uninstall in parallel pass -p,--parallel.

```
podman run quay.io/redhat_msi/ocp-addons-operators-cli \
    operators \
    --kubeconfig ~/work/CSPI/kubeconfig/rosa-myk412 \
    -o 'name=rhods-operator;namespace=redhat-ods-operator' \
    -o 'name=servicemeshoperator;timeout=600' \
    uninstall
```
