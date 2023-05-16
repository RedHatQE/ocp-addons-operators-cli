FROM python

RUN curl -L https://mirror.openshift.com/pub/openshift-v4/clients/rosa/latest/rosa-linux.tar.gz --output /tmp/rosa-linux.tar.gz &&\
    tar xvf /tmp/rosa-linux.tar.gz --no-same-owner &&\
    mv rosa /usr/bin/rosa &&\
    chmod +x /usr/bin/rosa &&\
    rosa version

WORKDIR ocp-addons-operators-cli
COPY . .
RUN python3 -m pip install pip --upgrade \
    && python3 -m pip install poetry \
    && poetry config cache-dir /cnv-tests \
    && poetry config virtualenvs.in-project true \
    && poetry config installer.max-workers 10 \
    && poetry config --list \
    && poetry env remove --all \
    && poetry install \
    && poetry export --without-hashes -n

ENTRYPOINT ["poetry", "run", "python", "app/cli.py"]
