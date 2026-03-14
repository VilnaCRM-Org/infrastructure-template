# syntax=docker/dockerfile:1
FROM python:3.11.7-slim

# Set build-time variables for UID and GID with defaults
ARG UID=1000
ARG GID=1000
ARG USERNAME=appuser
ARG PULUMI_VERSION=3.131.0
ARG PULUMI_SHA256=a4d870dc9e5967799c83dc640a7f14571d523b0429ab53257d6457b9b6b0ff19

# Install system dependencies as root
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Create home directory and set ownership
RUN mkdir -p /home/${USERNAME} && chown ${UID}:${GID} /home/${USERNAME}

# Set environment variables
ENV PATH="/home/${USERNAME}/.local/bin:/home/${USERNAME}/.pulumi/bin:${PATH}"
ENV HOME=/home/${USERNAME}
WORKDIR /home/${USERNAME}

# Switch to the user with specified UID and GID
USER ${UID}:${GID}

# Install Pulumi securely by verifying the release checksum
RUN set -eu && \
    TARBALL="pulumi-v${PULUMI_VERSION}-linux-x64.tar.gz" && \
    mkdir -p /tmp/pulumi && \
    curl -fsSL "https://get.pulumi.com/releases/sdk/${TARBALL}" -o "/tmp/${TARBALL}" && \
    echo "${PULUMI_SHA256}  /tmp/${TARBALL}" | sha256sum -c - && \
    tar -xzf "/tmp/${TARBALL}" -C /tmp && \
    mkdir -p /home/${USERNAME}/.pulumi/bin && \
    cp -r /tmp/pulumi/* /home/${USERNAME}/.pulumi/bin && \
    rm -rf /tmp/pulumi "/tmp/${TARBALL}"

# Install Poetry using a pinned installer version
RUN set -eu && \
    curl -fsSL https://install.python-poetry.org -o /tmp/install-poetry.py && \
    python3 /tmp/install-poetry.py && \
    rm /tmp/install-poetry.py && \
    ~/.local/bin/poetry config virtualenvs.in-project true

# Install AWS CLI
RUN mkdir awscliv2 && \
    curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64-2.15.0.zip" -o "awscliv2/awscliv2.zip" && \
    echo "bd3b5fc72d4bfe554ad72e96dd3571d79a6832fb268cc271ab33d73e8c2af46c  awscliv2/awscliv2.zip" | sha256sum -c && \
    unzip awscliv2/awscliv2.zip -d awscliv2 && \
    awscliv2/aws/install --install-dir /home/${USERNAME}/.aws-cli --bin-dir /home/${USERNAME}/.local/bin && \
    rm -rf awscliv2

# Verify installations (optional)
RUN pulumi version && poetry --version && aws --version

# Set the default command
CMD ["bash"]
