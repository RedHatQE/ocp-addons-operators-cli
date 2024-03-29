FROM python:3.12

# Install the Rosa CLI
RUN curl -L https://mirror.openshift.com/pub/openshift-v4/clients/rosa/latest/rosa-linux.tar.gz --output /tmp/rosa-linux.tar.gz \
  && tar xvf /tmp/rosa-linux.tar.gz --no-same-owner \
  && mv rosa /usr/bin/rosa \
  && chmod +x /usr/bin/rosa \
  && rosa version

# Install the OpenShift CLI (OC)
RUN curl -L https://mirror.openshift.com/pub/openshift-v4/x86_64/clients/ocp/stable/openshift-client-linux.tar.gz --output /tmp/openshift-client-linux.tar.gz \
  && tar xvf /tmp/openshift-client-linux.tar.gz --no-same-owner \
  && mv oc /usr/bin/oc \
  && mv kubectl /usr/bin/kubectl \
  && chmod +x /usr/bin/oc \
  && chmod +x /usr/bin/kubectl

COPY pyproject.toml poetry.lock README.md /ocp-addons-operators-cli/
COPY ocp_addons_operators_cli /ocp-addons-operators-cli/ocp_addons_operators_cli/

WORKDIR /ocp-addons-operators-cli

ENV POETRY_HOME=/ocp-addons-operators-cli
ENV PATH="/ocp-addons-operators-cli/bin:$PATH"

RUN python3 -m pip install pip --upgrade \
  && python3 -m pip install poetry \
  && poetry config cache-dir /ocp-addons-operators-cli \
  && poetry config virtualenvs.in-project true \
  && poetry config installer.max-workers 10 \
  && poetry config --list \
  && poetry install

ENTRYPOINT ["poetry", "run", "python", "ocp_addons_operators_cli/cli.py"]
