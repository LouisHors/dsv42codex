# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

This project is a local FastAPI adapter that bridges Codex through cc-switch to the DeepSeek `chat/completions` API. It accepts OpenAI-style `responses` requests, translates them into upstream `chat/completions` calls, and converts the upstream result back into `responses` format.

Target users are Chinese-speaking developers on Windows and macOS.

## Current Layout

```text
启动中转工具.command    macOS launcher
启动中转工具.bat        Windows launcher
src/
├── main.py             Uvicorn entrypoint
├── window_app.py       Desktop GUI
├── requirements.txt    Python dependencies
└── ds_adapter/
    ├── app.py          FastAPI app, routes, streaming, trace log
    ├── translator.py   Request/response translation logic
    ├── config.py       Runtime settings from environment variables
    ├── defaults.py     Default constants
    └── integration.py  CC Switch deeplink and Codex config helpers
tests/                  unittest test suite
build/                  PyInstaller specs and build artifacts
```

## Key Behavior

- The adapter exposes a local OpenAI-style endpoint at `http://127.0.0.1:9468/v1`.
- `/v1/responses` is the main endpoint and is translated to DeepSeek `chat/completions`.
- The adapter always sends `settings.upstream_model` to the upstream API, regardless of the downstream requested model.
- Streaming for `/v1/responses` is real SSE passthrough from the upstream stream.
- `/v1/chat/completions` exists mainly for debugging and is forced to non-stream behavior.
- GUI config is stored at `src/window_config.json`.
- Request tracing is written to `adapter_request_trace.jsonl` at the repository root.

## Commands

### Run the GUI

macOS:

```bash
cd src
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python window_app.py
```

Windows:

```powershell
cd src
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python window_app.py
```

### Run the adapter directly

From `src/`:

macOS:

```bash
python -m uvicorn main:app --host 127.0.0.1 --port 9468
```

Windows:

```powershell
.venv\Scripts\python -m uvicorn main:app --host 127.0.0.1 --port 9468
```

### Run tests

Prefer the project virtual environment:

macOS:

```bash
src/.venv/bin/python -m unittest discover -s tests -v
```

Windows:

```powershell
src\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Important Files

- `src/ds_adapter/app.py` contains the FastAPI app factory, admin endpoints, `/v1/responses`, `/v1/chat/completions`, SSE handling, and trace logging.
- `src/ds_adapter/translator.py` contains the pure protocol translation layer.
- `src/ds_adapter/integration.py` handles cc-switch deeplinks and Codex config patching.
- `src/window_app.py` is the desktop control surface used by end users.

## Testing Notes

- Tests use `unittest` plus `fastapi.testclient.TestClient`.
- Tests add `src/` to `sys.path` so they can import the package after the source tree move.
- `FakeUpstreamClient` is used to avoid real network requests.
