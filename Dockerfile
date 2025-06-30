FROM python:3.13

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

COPY pyproject.toml uv.lock README.md /ocp-addons-operators-cli/
COPY ocp_addons_operators_cli /ocp-addons-operators-cli/ocp_addons_operators_cli/

WORKDIR /ocp-addons-operators-cli

ENV UV_PYTHON=python3.13
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_SYNC=1
ENV UV_CACHE_DIR=${APP_DIR}/.cache

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/bin/
ENV PATH="/ocp-addons-operators-cli/bin:$PATH"

RUN uv sync
RUN chgrp -R 0 ${APP_DIR}/.cache && \
    chmod -R g=u ${APP_DIR}/.cache

ENTRYPOINT ["uv", "run", "ocp_addons_operators_cli/cli.py"]
