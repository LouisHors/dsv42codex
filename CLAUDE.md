# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A local FastAPI adapter that bridges Codex (via cc-switch) to the DeepSeek chat/completions API. It accepts OpenAI-style `responses` requests and translates them into upstream `chat/completions` calls, then wraps the response back into `responses` format. Supports both Windows and macOS. The target user is Chinese-speaking developers.

## Commands

```bash
# Install dependencies
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Windows
# source .venv/bin/activate && pip install -r requirements.txt  # macOS/Linux

# Run the adapter
.venv/Scripts/python -m uvicorn main:app --host 127.0.0.1 --port 9468   # Windows
# python -m uvicorn main:app --host 127.0.0.1 --port 9468               # macOS

# Run all tests
.venv/Scripts/python -m unittest discover -s tests -v   # Windows
# python -m unittest discover -s tests -v               # macOS

# Run a single test file
.venv/Scripts/python -m unittest tests.test_app -v
.venv/Scripts/python -m unittest tests.test_app.AdapterTests.test_models_endpoint -v

# Run the desktop GUI
.venv/Scripts/python window_app.py                       # Windows
# python window_app.py                                   # macOS
```

## Architecture

```
Request flow: Codex → cc-switch → this adapter (localhost:9468) → DeepSeek API
```

### Module responsibilities

- **`main.py`** — Uvicorn entrypoint, imports `app` from `ds_adapter.app`.
- **`ds_adapter/app.py`** — FastAPI application factory (`create_app`). Defines all HTTP routes, the `UpstreamClient` (httpx-based upstream caller), SSE streaming (`EventWriter`), request tracing (JSONL log), and the inline HTML config page. The app instance and settings live on `app.state`.
- **`ds_adapter/translator.py`** — Pure translation logic: converts OpenAI `responses` payloads into `chat/completions` payloads and vice versa. Handles input→message conversion, tool normalization (sanitizing names, wrapping non-function tools), reasoning effort mapping, `json_schema`→`json_object` downgrade, and streaming chunk synthesis.
- **`ds_adapter/config.py`** — `Settings` dataclass loaded from environment variables via `from_env()`. Also used for runtime config changes via the admin endpoints.
- **`ds_adapter/defaults.py`** — Default constants (base URL, model name, chat path).
- **`ds_adapter/integration.py`** — CC Switch deeplink generation (`ccswitch://` protocol), Codex `config.toml` patching, and protocol detection. Uses `winreg` on Windows; on macOS, delegates to `webbrowser.open()` for `ccswitch://` URL handling.
- **`window_app.py`** — Desktop GUI (tkinter) for managing settings, starting/stopping the adapter, and triggering CC Switch import. Cross-platform: uses platform-appropriate fonts (`UI_FONT` / `MONO_FONT` constants).

### Key design decisions

- The adapter always sends `model: settings.upstream_model` to DeepSeek, ignoring whatever model the downstream client requested. The original model name is preserved in the response for client compatibility.
- Streaming mode for `/v1/responses` is real passthrough from the upstream SSE stream. Streaming for `/v1/chat/completions` is forced to non-stream (the endpoint is for debugging only).
- DeepSeek's `json_schema` response format is unavailable, so it's downgraded to `json_object` with the schema injected as text instructions.
- Non-function tools (custom tools) are wrapped into a single-string function schema so the tool-call chain can be tested.
- Tool names are sanitized to `[-A-Za-z0-9_]` with a SHA1 digest suffix to avoid upstream rejection while preserving a mapping back to original names.
- For DeepSeek V4 models with tool-heavy replayed conversations, default thinking mode is disabled to avoid `reasoning_content` passthrough issues.

### API endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/` | GET | Web config page (inline HTML) |
| `/health` | GET | Health check |
| `/v1/models` | GET | Lists adapter model IDs |
| `/v1/responses` | POST | Main entry — translates to upstream chat/completions |
| `/v1/chat/completions` | POST | Non-stream passthrough (debugging) |
| `/admin/config` | GET/POST | Read/update runtime settings |
| `/admin/test-upstream` | POST | Probe upstream connectivity |

### Testing approach

Tests use `FakeUpstreamClient` injected via `create_app(settings=..., upstream_client=...)`. This avoids real HTTP calls. Tests are in `unittest` style with `fastapi.testclient.TestClient`.

## Environment Variables

See `.env.example` for the full list. Key ones:

- `UPSTREAM_BASE_URL` — DeepSeek API base URL (default: `https://api.deepseek.com`)
- `UPSTREAM_MODEL` — Model sent to upstream (default: `deepseek-v4-pro`)
- `ADAPTER_MODEL_IDS` — Comma-separated model IDs exposed to clients
- `UPSTREAM_API_KEY` — Optional; if unset, the adapter forwards the inbound `Authorization` header
