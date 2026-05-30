#!/usr/bin/env sh
set -e

uv lock
docker compose up -d --build
