#!/usr/bin/env bats

# Unit-level checks for the Makefile interface. These tests inspect commands with dry runs so we
# do not require Docker or cloud credentials during CI.

assert_compose_env_file() {
  [[ "$output" == *"docker compose --env-file .env "* ]] \
    || [[ "$output" == *"docker compose --env-file .env.empty "* ]]
}

@test "make help lists every public target" {
  run make help
  [ "$status" -eq 0 ]
  [[ "$output" == *"all"* ]]
  [[ "$output" == *"clean"* ]]
  [[ "$output" == *"down"* ]]
  [[ "$output" == *"help"* ]]
  [[ "$output" == *"pulumi"* ]]
  [[ "$output" == *"pulumi-preview"* ]]
  [[ "$output" == *"pulumi-up"* ]]
  [[ "$output" == *"pulumi-refresh"* ]]
  [[ "$output" == *"pulumi-destroy"* ]]
  [[ "$output" == *"sh"* ]]
  [[ "$output" == *"start"* ]]
  [[ "$output" == *"test"* ]]
  [[ "$output" == *"test-cli"* ]]
  [[ "$output" == *"test-integration"* ]]
  [[ "$output" == *"test-mutation"* ]]
  [[ "$output" == *"test-pulumi"* ]]
  [[ "$output" == *"test-unit"* ]]
}

@test "make all delegates to the help output" {
  run make all
  [ "$status" -eq 0 ]
  [[ "$output" == *"Usage:"* ]]
  [[ "$output" == *"Targets:"* ]]
}

@test "make start uses docker compose with .env" {
  run make -n start
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"up -d"* ]]
}

@test "make pulumi proxies arbitrary Pulumi commands inside the container" {
  run make -n pulumi ARGS="version"
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"pulumi --cwd pulumi version"* ]]
}

@test "make pulumi-preview executes preview inside container" {
  run make -n pulumi-preview
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"pulumi --cwd pulumi preview"* ]]
}

@test "make pulumi-up executes deployment inside container" {
  run make -n pulumi-up
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"pulumi --cwd pulumi up"* ]]
}

@test "make pulumi-refresh executes refresh inside container" {
  run make -n pulumi-refresh
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"pulumi --cwd pulumi refresh"* ]]
}

@test "make pulumi-destroy executes destroy inside container" {
  run make -n pulumi-destroy
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"pulumi --cwd pulumi destroy"* ]]
}

@test "make sh opens a throwaway shell in the Pulumi container" {
  run make -n sh
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"run --rm pulumi sh"* ]]
}

@test "make down stops docker compose without depending on the env file" {
  run make -n down
  [ "$status" -eq 0 ]
  [[ "$output" == *"docker compose down"* ]]
  [[ "$output" != *"--env-file"* ]]
}

@test "make test-unit executes the unit suite with coverage" {
  run make -n test-unit
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"pytest -q tests/unit"* ]]
  [[ "$output" == *"PYTEST_ADDOPTS="* ]]
}

@test "make test-integration executes the integration suite and coverage merge" {
  run make -n test-integration
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"pytest -q tests/integration"* ]]
  [[ "$output" == *"coverage combine"* ]]
  [[ "$output" == *"coverage report --show-missing"* ]]
}

@test "make test-pulumi executes the structural suite" {
  run make -n test-pulumi
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"pytest -q tests/pulumi"* ]]
}

@test "make test-mutation executes the mutation helper script" {
  run make -n test-mutation
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"./scripts/run_mutation_tests.sh"* ]]
}

@test "make test-cli runs the Bats suite inside the container" {
  run make -n test-cli
  [ "$status" -eq 0 ]
  assert_compose_env_file
  [[ "$output" == *"COMPOSE_TARGET=test"* ]]
  [[ "$output" == *"bats tests/unit"* ]]
}

@test "make test runs the aggregate local battery" {
  run make -n test
  [ "$status" -eq 0 ]
  [[ "$output" == *"make test-pulumi"* ]]
  [[ "$output" == *"make test-unit"* ]]
  [[ "$output" == *"make test-integration"* ]]
  [[ "$output" == *"make test-cli"* ]]
}

@test "make clean removes compose state and Python build artifacts" {
  run make -n clean
  [ "$status" -eq 0 ]
  [[ "$output" == *"docker compose down -v"* ]]
  [[ "$output" == *"find . -type d -name __pycache__"* ]]
  [[ "$output" == *"find . -type f -name \"*.pyc\""* ]]
  [[ "$output" == *"rm -rf .venv dist build *.egg-info"* ]]
}
