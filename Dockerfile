# syntax=docker/dockerfile:1.7-labs

ARG BASE_IMAGE=python:3.11.9-slim-bookworm@sha256:8fb099199b9f2d70342674bd9dbccd3ed03a258f26bbd1d556822c6dfc60c317
FROM ${BASE_IMAGE} AS base

ARG USERNAME=dev
ARG UID=1000
ARG GID=1000
ARG PULUMI_VERSION=3.131.0
ARG PULUMI_SHA256=a4d870dc9e5967799c83dc640a7f14571d523b0429ab53257d6457b9b6b0ff19
ARG AWSCLI_VERSION=2.15.0
ARG AWSCLI_ARCH=linux-x86_64
ARG AWSCLI_SHA256=bd3b5fc72d4bfe554ad72e96dd3571d79a6832fb268cc271ab33d73e8c2af46c
ARG POETRY_VERSION=1.8.4
ARG POETRY_INSTALLER_SHA256=963d56703976ce9cdc6ff460c44a4f8fbad64c110dc447b86eeabb4a47ec2160
ENV DEBIAN_FRONTEND=noninteractive

RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\n' > /etc/apt/apt.conf.d/99retries \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        unzip \
        git \
        make \
        bash \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid "${GID}" "${USERNAME}" \
    && useradd --uid "${UID}" --gid "${GID}" --create-home "${USERNAME}"

RUN bash -o pipefail -c 'curl --fail --silent --show-error --location \
        --retry 5 --retry-delay 5 --retry-all-errors \
        "https://get.pulumi.com/releases/sdk/pulumi-v${PULUMI_VERSION}-linux-x64.tar.gz" \
        --output /tmp/pulumi.tar.gz \
    && echo "${PULUMI_SHA256}  /tmp/pulumi.tar.gz" | sha256sum -c - \
    && mkdir -p /opt/pulumi \
    && tar --extract --gzip --file /tmp/pulumi.tar.gz --strip-components=1 --directory /opt/pulumi \
    && ln -sf /opt/pulumi/pulumi /usr/local/bin/pulumi \
    && rm -f /tmp/pulumi.tar.gz'

RUN bash -o pipefail -c "set -euo pipefail \
    && curl --fail --silent --show-error --location \
        --retry 5 --retry-delay 5 --retry-all-errors \
        \"https://awscli.amazonaws.com/awscli-exe-${AWSCLI_ARCH}-${AWSCLI_VERSION}.zip\" \
        --output /tmp/awscliv2.zip \
    && echo \"${AWSCLI_SHA256}  /tmp/awscliv2.zip\" | sha256sum -c - \
    && unzip /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli \
    && rm -rf /tmp/aws /tmp/awscliv2.zip"

ENV POETRY_HOME=/opt/poetry
ENV PATH="/opt/pulumi:${POETRY_HOME}/bin:/home/${USERNAME}/.local/bin:${PATH}"

RUN bash -o pipefail -c 'curl --fail --silent --show-error --location \
        --retry 5 --retry-delay 5 --retry-all-errors \
        https://install.python-poetry.org \
        --output /tmp/install-poetry.py \
    && echo "${POETRY_INSTALLER_SHA256}  /tmp/install-poetry.py" | sha256sum -c - \
    && python /tmp/install-poetry.py --version "${POETRY_VERSION}" \
    && rm -f /tmp/install-poetry.py'

ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_HTTP_TIMEOUT=60

FROM base AS dev

ARG USERNAME=dev
ARG GID=1000

RUN mkdir -p /workspace/pulumi
COPY --chown=${USERNAME}:${GID} pulumi/pyproject.toml pulumi/poetry.lock /workspace/pulumi/

WORKDIR /workspace

RUN --mount=type=cache,target=/root/.cache/pypoetry \
    poetry config installer.max-workers 4 \
    && poetry -C /workspace/pulumi install --no-root --no-interaction --no-ansi --with dev

USER "${USERNAME}"
WORKDIR /workspace
ENV HOME=/home/${USERNAME}

CMD ["bash"]

FROM dev AS test

ARG USERNAME=dev
ARG BATS_VERSION=1.11.0
ARG BATS_SHA256=aeff09fdc8b0c88b3087c99de00cf549356d7a2f6a69e3fcec5e0e861d2f9063

USER root

RUN bash -o pipefail -c 'curl --fail --silent --show-error --location \
        --retry 5 --retry-delay 5 --retry-all-errors \
        "https://github.com/bats-core/bats-core/archive/refs/tags/v${BATS_VERSION}.tar.gz" \
        --output /tmp/bats.tar.gz \
    && echo "${BATS_SHA256}  /tmp/bats.tar.gz" | sha256sum -c - \
    && tar --extract --gzip --file /tmp/bats.tar.gz --directory /tmp \
    && /tmp/bats-core-${BATS_VERSION}/install.sh /usr/local \
    && rm -rf /tmp/bats.tar.gz /tmp/bats-core-${BATS_VERSION}'

USER "${USERNAME}"
