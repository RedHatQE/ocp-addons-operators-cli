FROM python:3.11

RUN curl -L https://mirror.openshift.com/pub/openshift-v4/clients/rosa/latest/rosa-linux.tar.gz --output /tmp/rosa-linux.tar.gz \
    && tar xvf /tmp/rosa-linux.tar.gz --no-same-owner \
    && mv rosa /usr/bin/rosa \
    && chmod +x /usr/bin/rosa \
    && rosa version

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
    && poetry install \
    && poetry export --without-hashes -n

ENTRYPOINT ["poetry", "run", "python", "ocp_addons_operators_cli/cli.py"]
