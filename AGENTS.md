# AGENTS.md

This file provides guidance to coding agents working in this repository.

## Project Summary

DSV4 local adapter is a FastAPI-based bridge between Codex, cc-switch, and DeepSeek. The adapter accepts OpenAI-style `responses` requests from downstream clients and translates them into DeepSeek-compatible `chat/completions` requests.

The current codebase is organized under `src/`, with a desktop GUI for end users and a unittest suite under `tests/`.

## Source of Truth

- Public project documentation should live in `README.md`.
- Agent-facing repo guidance lives in this file and `CLAUDE.md`.
- Do not create extra standalone project explanation documents unless explicitly requested.

## Repository Layout

```text
src/
  main.py
  window_app.py
  requirements.txt
  ds_adapter/
tests/
build/
启动中转工具.command
启动中转工具.bat
```

## Current Runtime Assumptions

- Local adapter URL: `http://127.0.0.1:9468/v1`
- Default upstream base URL: `https://api.deepseek.com`
- Default upstream path: `/chat/completions`
- Default upstream model: `deepseek-v4-pro`
- Alternate GUI model option: `deepseek-v4-flash`

## Working Notes

- The project has recently moved source files into `src/`; keep docs, scripts, tests, and paths aligned with that layout.
- GUI launcher scripts create and use `src/.venv`.
- `src/window_config.json` is runtime GUI state, not primary documentation.
- `adapter_request_trace.jsonl` is emitted at the repository root.

## Useful Commands

Run GUI:

```bash
cd src
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python window_app.py
```

Run tests on macOS:

```bash
src/.venv/bin/python -m unittest discover -s tests -v
```

Run tests on Windows:

```powershell
src\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## Editing Guidance

- Keep `README.md`, `CLAUDE.md`, and `AGENTS.md` consistent when repository structure or operational behavior changes.
- Prefer concise user-facing documentation in `README.md`; keep deep implementation detail in agent-facing docs only when useful.
- Avoid reintroducing duplicate end-user documentation files under build artifacts unless the user explicitly asks for them.
