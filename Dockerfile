# syntax=docker/dockerfile:1.7-labs

# Debian slim keeps the image small while remaining compatible with AWS CLI v2.
ARG BASE_IMAGE=python:3.11.9-slim-bookworm@sha256:8fb099199b9f2d70342674bd9dbccd3ed03a258f26bbd1d556822c6dfc60c317
FROM ${BASE_IMAGE} AS tooling

ARG TARGETARCH=amd64
ARG USERNAME=dev
ARG UID=1000
ARG GID=1000
ARG PULUMI_VERSION=3.138.0
ARG PULUMI_SHA256_AMD64=00245ee263285ee05ff33ec96c889aa4d1171e0c8eb0366a64205b45eafd6ed8
ARG PULUMI_SHA256_ARM64=905106b80be34963361737b6c4d471b45d77461c3455b137cefd66b2c470566c
ARG AWSCLI_VERSION=2.16.9
ARG AWSCLI_SHA256_AMD64=8c09f0aa7743fb04a28ac7a6f3c2822d6ffcc58bcace2beaf55258ee0f67c4cb
ARG AWSCLI_SHA256_ARM64=82636f7ec20c57beeed19a14f8684113e0edfb30e79f1a615809de2dfb482712
ARG CA_CERTIFICATES_VERSION=20230311
ARG UNZIP_VERSION=6.0-28
ARG CURL_VERSION=7.88.1-10+deb12u14
ARG UV_VERSION=0.9.21
ARG UV_SHA256_AMD64=0a1ab27383c28ef1c041f85cbbc609d8e3752dfb4b238d2ad97b208a52232baf
ARG UV_SHA256_ARM64=416984484783a357170c43f98e7d2d203f1fb595d6b3b95131513c53e50986ef
ENV DEBIAN_FRONTEND=noninteractive

# Install only the transient packages required to download and unpack tooling.
RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\n' > /etc/apt/apt.conf.d/99retries \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates="${CA_CERTIFICATES_VERSION}" \
        curl="${CURL_VERSION}" \
        unzip="${UNZIP_VERSION}" \
    && rm -rf /var/lib/apt/lists/*

# Install Pulumi CLI once and expose it on the PATH for all users
RUN bash -o pipefail -c 'set -euo pipefail \
    && case "${TARGETARCH}" in \
        amd64) pulumi_arch="x64"; pulumi_sha256="${PULUMI_SHA256_AMD64}" ;; \
        arm64) pulumi_arch="arm64"; pulumi_sha256="${PULUMI_SHA256_ARM64}" ;; \
        *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && curl --fail --silent --show-error --location \
        --retry 5 --retry-delay 5 --retry-all-errors \
        "https://get.pulumi.com/releases/sdk/pulumi-v${PULUMI_VERSION}-linux-${pulumi_arch}.tar.gz" \
        --output /tmp/pulumi.tar.gz \
    && echo "${pulumi_sha256}  /tmp/pulumi.tar.gz" | sha256sum -c - \
    && mkdir -p /opt/pulumi \
    && tar --extract --gzip --file /tmp/pulumi.tar.gz --strip-components=1 --directory /opt/pulumi \
    && rm -f \
        /opt/pulumi/pulumi-language-dotnet \
        /opt/pulumi/pulumi-language-go \
        /opt/pulumi/pulumi-language-java \
        /opt/pulumi/pulumi-language-nodejs \
        /opt/pulumi/pulumi-language-yaml \
        /opt/pulumi/pulumi-resource-pulumi-nodejs \
        /opt/pulumi/pulumi-watch \
    && rm -rf /tmp/pulumi.tar.gz'

# Install AWS CLI v2
RUN bash -o pipefail -c 'set -euo pipefail \
    && case "${TARGETARCH}" in \
        amd64) awscli_arch="linux-x86_64"; awscli_sha256="${AWSCLI_SHA256_AMD64}" ;; \
        arm64) awscli_arch="linux-aarch64"; awscli_sha256="${AWSCLI_SHA256_ARM64}" ;; \
        *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && curl --fail --silent --show-error --location \
        --retry 5 --retry-delay 5 --retry-all-errors \
        "https://awscli.amazonaws.com/awscli-exe-${awscli_arch}-${AWSCLI_VERSION}.zip" \
        --output "/tmp/awscliv2.zip" \
    && echo "${awscli_sha256}  /tmp/awscliv2.zip" | sha256sum -c - \
    && unzip /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install --bin-dir /usr/local/bin --install-dir /usr/local/aws-cli \
    && rm -rf /usr/local/aws-cli/v2/current/dist/awscli/examples \
    && rm -rf /tmp/aws /tmp/awscliv2.zip'

# Install uv for dependency management and command execution
RUN bash -o pipefail -c 'set -euo pipefail \
    && case "${TARGETARCH}" in \
        amd64) uv_arch="x86_64-unknown-linux-gnu"; uv_sha256="${UV_SHA256_AMD64}" ;; \
        arm64) uv_arch="aarch64-unknown-linux-gnu"; uv_sha256="${UV_SHA256_ARM64}" ;; \
        *) echo "Unsupported TARGETARCH: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && curl --fail --silent --show-error --location \
        --retry 5 --retry-delay 5 --retry-all-errors \
        "https://github.com/astral-sh/uv/releases/download/${UV_VERSION}/uv-${uv_arch}.tar.gz" \
        --output /tmp/uv.tar.gz \
    && echo "${uv_sha256}  /tmp/uv.tar.gz" | sha256sum -c - \
    && tar --extract --gzip --file /tmp/uv.tar.gz --directory /tmp \
    && install -m 0755 "/tmp/uv-${uv_arch}/uv" /usr/local/bin/uv \
    && install -m 0755 "/tmp/uv-${uv_arch}/uvx" /usr/local/bin/uvx \
    && rm -rf /tmp/uv.tar.gz "/tmp/uv-${uv_arch}"'

FROM ${BASE_IMAGE} AS runtime-base

ARG TARGETARCH=amd64
ARG USERNAME=dev
ARG UID=1000
ARG GID=1000
ARG CA_CERTIFICATES_VERSION=20230311
ARG MAKE_VERSION=4.3-4.1
ENV DEBIAN_FRONTEND=noninteractive
ENV HOME=/home/${USERNAME}
ENV PATH="/opt/pulumi:/home/${USERNAME}/.local/bin:/home/${USERNAME}/.pulumi/bin:${PATH}"
ENV AWS_PAGER=""
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PULUMI_HOME=${HOME}/.pulumi
ENV PULUMI_SKIP_UPDATE_CHECK=true
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_LINK_MODE=copy
ENV UV_CACHE_DIR=${HOME}/.cache/uv
ENV UV_PROJECT_ENVIRONMENT=${HOME}/.venvs/infrastructure-template
ENV PULUMI_PYTHON_CMD=${UV_PROJECT_ENVIRONMENT}/bin/python

RUN printf 'Acquire::Retries "5";\nAcquire::http::Timeout "30";\n' > /etc/apt/apt.conf.d/99retries \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates="${CA_CERTIFICATES_VERSION}" \
        make="${MAKE_VERSION}" \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid "${GID}" "${USERNAME}" \
    && useradd --uid "${UID}" --gid "${GID}" --create-home "${USERNAME}"

COPY --from=tooling /opt/pulumi /opt/pulumi
COPY --from=tooling /usr/local/aws-cli /usr/local/aws-cli
COPY --from=tooling /usr/local/bin/uv /usr/local/bin/uv
COPY --from=tooling /usr/local/bin/uvx /usr/local/bin/uvx

RUN ln -sf /opt/pulumi/pulumi /usr/local/bin/pulumi \
    && ln -sf /usr/local/aws-cli/v2/current/bin/aws /usr/local/bin/aws \
    && ln -sf /usr/local/aws-cli/v2/current/bin/aws_completer /usr/local/bin/aws_completer

FROM runtime-base AS dev

# Keep the uv-managed environment outside /workspace so bind mounts never hide it.
RUN install -d -o "${USERNAME}" -g "${GID}" \
        "${HOME}/.cache/uv" \
        "${HOME}/.venvs" \
        "${PULUMI_HOME}"

COPY --chown=${USERNAME}:${GID} pyproject.toml uv.lock /workspace/

WORKDIR /workspace

RUN --mount=type=cache,target=/home/${USERNAME}/.cache/uv,uid=${UID},gid=${GID} \
    uv venv --seed "${UV_PROJECT_ENVIRONMENT}" \
    && uv sync --frozen --all-groups \
    && chown -R "${USERNAME}:${GID}" "${UV_CACHE_DIR}" \
    && chown -R "${USERNAME}:${GID}" "${UV_PROJECT_ENVIRONMENT}"

USER "${USERNAME}"
WORKDIR /workspace

# Pulumi CLI caches a few files under the user's home directory
CMD ["bash"]

FROM tooling AS bats-installer
ARG BATS_VERSION=1.11.0
ARG BATS_SHA256=aeff09fdc8b0c88b3087c99de00cf549356d7a2f6a69e3fcec5e0e861d2f9063

RUN bash -o pipefail -c 'curl --fail --silent --show-error --location \
        --retry 5 --retry-delay 5 --retry-all-errors \
        "https://github.com/bats-core/bats-core/archive/refs/tags/v${BATS_VERSION}.tar.gz" \
        --output /tmp/bats.tar.gz \
    && echo "${BATS_SHA256}  /tmp/bats.tar.gz" | sha256sum -c - \
    && tar --extract --gzip --file /tmp/bats.tar.gz --directory /tmp \
    && /tmp/bats-core-${BATS_VERSION}/install.sh /opt/bats \
    && rm -rf /tmp/bats.tar.gz /tmp/bats-core-${BATS_VERSION}'

FROM dev AS test

USER root
COPY --from=bats-installer /opt/bats /usr/local

USER "${USERNAME}"
