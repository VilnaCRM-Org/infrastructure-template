# syntax=docker/dockerfile:1.7-labs

FROM python:3.11.9-slim

ARG USERNAME=dev
ARG UID=1000
ARG GID=1000

ENV DEBIAN_FRONTEND=noninteractive

# Install OS dependencies required for Pulumi CLI and Python tooling
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user that mirrors the host developer UID/GID
RUN groupadd --gid "${GID}" "${USERNAME}" \
    && useradd --uid "${UID}" --gid "${GID}" --create-home "${USERNAME}"

# Create a dedicated virtual environment for Python packages
RUN python -m venv /opt/pulumi-venv
ENV VIRTUAL_ENV=/opt/pulumi-venv
ENV PATH="$VIRTUAL_ENV/bin:/home/${USERNAME}/.pulumi/bin:${PATH}"

# Install Pulumi CLI
RUN curl -fsSL https://get.pulumi.com | sh

# Install Python dependencies used by the Pulumi project and linting tooling
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir \
        "pulumi>=3.138,<4" \
        "pulumi-aws>=7.0,<8" \
        black \
        flake8 \
        pre-commit

USER "${USERNAME}"
WORKDIR /workspace

# Pulumi CLI caches a few files under the user's home directory
ENV HOME=/home/${USERNAME}

CMD ["bash"]
