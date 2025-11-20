# Mem0 API Tests

This directory contains test scripts for the Mem0 API server.

## Prerequisites

- [uv](https://github.com/astral-sh/uv) installed.

## Running Tests

Run the test script using `uv run`:

```bash
cd tests
uv run test_api.py
```

`uv` will automatically create a virtual environment and install the required dependencies (`requests`) defined in `pyproject.toml`.
重新执行重启命令