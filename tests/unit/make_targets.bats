#!/usr/bin/env bats

# Dry-run the Makefile surface so CLI regressions are caught without requiring live infrastructure.

@test "make help lists Pulumi-oriented validation targets" {
  run make help
  [ "$status" -eq 0 ]
  [[ "$output" == *"pulumi-preview"* ]]
  [[ "$output" == *"test-pulumi"* ]]
  [[ "$output" == *"test-unit"* ]]
  [[ "$output" == *"test-integration"* ]]
  [[ "$output" == *"test-mutation"* ]]
  [[ "$output" == *"test-cli"* ]]
}

@test "make start uses docker compose with the fallback env file" {
  run make -n start
  [ "$status" -eq 0 ]
  [[ "$output" == *"docker compose --env-file .env up -d"* ]] \
    || [[ "$output" == *"docker compose --env-file .env.empty up -d"* ]]
}

@test "make pulumi-preview runs preview inside the workspace container" {
  run make -n pulumi-preview
  [ "$status" -eq 0 ]
  [[ "$output" == *"docker compose --env-file .env run --rm pulumi pulumi --cwd pulumi preview"* ]] \
    || [[ "$output" == *"docker compose --env-file .env.empty run --rm pulumi pulumi --cwd pulumi preview"* ]]
}

@test "make pulumi-up runs update inside the workspace container" {
  run make -n pulumi-up
  [ "$status" -eq 0 ]
  [[ "$output" == *"docker compose --env-file .env run --rm pulumi pulumi --cwd pulumi up"* ]] \
    || [[ "$output" == *"docker compose --env-file .env.empty run --rm pulumi pulumi --cwd pulumi up"* ]]
}

@test "make pulumi-refresh runs refresh inside the workspace container" {
  run make -n pulumi-refresh
  [ "$status" -eq 0 ]
  [[ "$output" == *"docker compose --env-file .env run --rm pulumi pulumi --cwd pulumi refresh"* ]] \
    || [[ "$output" == *"docker compose --env-file .env.empty run --rm pulumi pulumi --cwd pulumi refresh"* ]]
}

@test "make pulumi-destroy runs destroy inside the workspace container" {
  run make -n pulumi-destroy
  [ "$status" -eq 0 ]
  [[ "$output" == *"docker compose --env-file .env run --rm pulumi pulumi --cwd pulumi destroy"* ]] \
    || [[ "$output" == *"docker compose --env-file .env.empty run --rm pulumi pulumi --cwd pulumi destroy"* ]]
}

@test "make sh opens a throwaway shell in the workspace container" {
  run make -n sh
  [ "$status" -eq 0 ]
  [[ "$output" == *"docker compose --env-file .env run --rm pulumi sh"* ]] \
    || [[ "$output" == *"docker compose --env-file .env.empty run --rm pulumi sh"* ]]
}
