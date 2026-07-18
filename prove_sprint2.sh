#!/bin/bash
# Proof Harness Wrapper

echo "Starting test harness..."
# Ensure dependencies are available via the API's uv environment
cd apps/api
uv pip install httpx
uv run python ../../prove_sprint2.py
