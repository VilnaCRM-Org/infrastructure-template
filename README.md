# Infrastructure Template for Modern DevOps applications

[![SWUbanner](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://supportukrainenow.org/)

[![Pulumi Preview](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-preview.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-preview.yml)
[![Pulumi Deploy](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-deploy.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-deploy.yml)
[![Super Linter](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/super-linter.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/super-linter.yml)

Production-ready scaffold for teams that want to ship infrastructure-as-code with Pulumi and Docker from day zero.

## Possibilities

- Pulumi (Python) starter that provisions an AWS EC2 instance and exports connection metadata.
- Reproducible Docker Compose workspace with a Pulumi-ready container and helper `make` tasks.
- CI/CD pipelines for previews and deployments, powered by GitHub Actions and Pulumi Cloud.
- Built-in linting via GitHub Super Linter to keep YAML, Markdown, and workflows healthy.
- Documentation on AWS credential management for secure automation using GitHub OIDC or static secrets.

## Why You Might Need It

Spin up consistent project infrastructure without wiring every component manually. This template gives DevOps teams a single source that:

- Encodes best practices from VilnaCRM’s production stack.
- Works out-of-the-box with AWS and Pulumi.
- Keeps cloud changes reviewable with preview pipelines before production deploys.

## License

This software is distributed under the [Creative Commons Zero v1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/deed) license. Please read [`LICENSE`](LICENSE) for details.

## Quick Start

1. **Use this template** or clone the repository locally.
2. Install [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/).
3. (Optional) Install the [Pulumi CLI](https://www.pulumi.com/docs/install/) if you plan to run commands outside the container.
4. Launch the local environment:

   ```bash
   make start
   ```

5. Configure your AWS credentials (for example via `aws configure`, environment variables, or GitHub Actions secrets).
6. Run a preview from inside the container to validate infrastructure changes:

   ```bash
   make pulumi-preview
   ```

That is all you need to begin iterating on the sample AWS instance or adapting the stack to your own infrastructure.

## Local Tooling

`make help` prints the available tasks. Most common targets:

```text
start             Initialize and start the Pulumi development environment.
pulumi-preview    Preview infrastructure changes from inside the container.
pulumi-up         Apply the current infrastructure plan.
pulumi-refresh    Sync the Pulumi stack with live cloud resources.
pulumi-destroy    Tear down the stack (irreversible; use with caution).
sh                Open a shell inside the Pulumi container.
down              Stop the Docker Compose environment.
```

## Development

PyCharm autocomplete: create a local venv (`python3 -m venv pulumi/.venv`), install Pulumi deps, then add that interpreter via `Settings → Project → Python Interpreter → Add → Existing environment`.

```bash
python3 -m venv pulumi/.venv
source pulumi/.venv/bin/activate  # use the equivalent activate script on Windows
pip install --upgrade pip
pip install "pulumi>=3.138,<4" "pulumi-aws>=7.0,<8" black flake8 pre-commit
deactivate
```

Re-run the `pip install …` line whenever dependencies change, or recreate the venv after switching Python versions.

## CI/CD and Secrets

Two GitHub Actions workflows handle environment parity:

- `pulumi-preview.yml` evaluates changes on pull requests.
- `pulumi-deploy.yml` applies changes to the `dev` stack on `main`.

Both workflows require AWS and Pulumi credentials. Follow [`docs/github-actions-secrets.md`](docs/github-actions-secrets.md) to configure:

- `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` **or** a GitHub OIDC role.
- `PULUMI_ACCESS_TOKEN` for authenticating with the Pulumi Service.

Without these secrets the workflows will fail during the credential configuration stage.

## Project Structure

- `pulumi/__main__.py` – Minimal Pulumi program that provisions an EC2 instance and exports IDs/IPs.
- `docker-compose.yml` – Local development environment with Pulumi tooling baked in.
- `Makefile` – Convenience commands for build, preview, deploy, and container management.
- `.github/workflows` – Automation for previews, deploys, linting, and template synchronization.

## Documentation

Start with the [GitHub Wiki](https://github.com/VilnaCRM-Org/infrastructure-template/wiki) for deeper guides and troubleshooting tips. Community Q&A lives under the [`vilnacrm` tag on Stack Overflow](https://stackoverflow.com/questions/tagged/vilnacrm).

## Testing and Validation

Continuous integration runs automatically on every pull request. You can also validate locally:

- `make pulumi-preview` to review planned resources.
- `make pulumi-up` followed by `pulumi stack output` to inspect applied results.
- `pulumi stack history` (from inside the container) to audit state transitions.

## Repository Synchronization

This template feeds other VilnaCRM infrastructure projects through [`actions-template-sync`](https://github.com/AndreasAugustin/actions-template-sync). For authentication guidance, see:

- `.github/TEMPLATE_SYNC_PAT.md` for Personal Access Tokens.
- `.github/TEMPLATE_SYNC_APP.md` for GitHub App credentials.

Remember to grant least privilege, rotate secrets regularly, and monitor workflow logs.

## Security

Report security issues responsibly to the maintainers. Consult [`SECURITY.md`](SECURITY.md) and the repository’s [security advisories](https://github.com/VilnaCRM-Org/infrastructure-template/security).

## Contributing

Bug reports, feature requests, and pull requests are welcome via the [issue tracker](https://github.com/VilnaCRM-Org/infrastructure-template/issues). Documentation updates are highly appreciated—feel free to enhance the wiki or submit fixes directly.

## Sponsorship

Development time and resources for this repository are provided by [VilnaCRM](https://vilnacrm.com/), the free and opensource CRM system.

Donations are very welcome, whether in beer 🍺, T-shirts 👕, or cold, hard cash 💰. Sponsorship through GitHub is a simple and convenient way to say "thank you" to maintainers and contributors – just click the "Sponsor" button [on the project page](https://github.com/VilnaCRM-Org/infrastructure-template). If your company uses this template, consider taking part in the VilnaCRM's enterprise support program.
