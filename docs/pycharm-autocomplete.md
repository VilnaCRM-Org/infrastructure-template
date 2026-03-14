# PyCharm Autocomplete with the Docker Workspace

The repository ships with a Docker workspace that already contains Pulumi, Poetry, AWS CLI, and the Python dependencies from `pulumi/pyproject.toml`.

## 1. Start the workspace

```bash
docker compose up --build -d
```

The compose file exposes a single service named `pulumi` and mounts the repository into `/workspace`.

## 2. Attach PyCharm to the Docker interpreter

1. Open the repository in PyCharm.
2. Go to `Settings -> Project -> Python Interpreter`.
3. Click the gear icon -> `Add...` -> choose **Docker Compose**.
4. Select this repository's `docker-compose.yml`.
5. Choose the `pulumi` service.
6. Use `/usr/local/bin/python` as the interpreter path.

PyCharm will index the container interpreter and expose Pulumi/Python autocomplete without a local virtualenv.

## 3. Verify the environment

Open a terminal in the running container and check the core tools:

```bash
docker compose exec pulumi bash -lc 'pulumi version && poetry --version && python -c "import pulumi"'
```

## 4. Optional local fallback

If you cannot use Docker locally, create a virtual environment and install the same dependency set:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install poetry
poetry -C pulumi install --with dev
```

Point PyCharm to `.venv/bin/python` after that.
