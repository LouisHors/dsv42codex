# DSV4 本地中转工具

DSV4 Local Adapter

一个面向中文开发者的本地适配器，用来把 Codex 经由 cc-switch 发出的 OpenAI `responses` 请求，转成 DeepSeek 兼容的 `chat/completions` 请求。

A local adapter for Chinese-speaking developers that converts OpenAI-style `responses` requests from Codex via cc-switch into DeepSeek-compatible `chat/completions` requests.

请求链路 / Request flow:

`Codex -> cc-switch -> 本地适配器 / local adapter -> DeepSeek`

支持 Windows 和 macOS。

Supports Windows and macOS.

## 功能简介 / Features

- 提供本地 OpenAI 风格接口，默认地址为 `http://127.0.0.1:9468/v1`
- Exposes a local OpenAI-style endpoint at `http://127.0.0.1:9468/v1`
- 将 `/v1/responses` 翻译为 DeepSeek `chat/completions`
- Translates `/v1/responses` into DeepSeek `chat/completions`
- 提供桌面 GUI，便于填写上游配置、测试连通性和导入 CC Switch
- Includes a desktop GUI for upstream config, connectivity checks, and CC Switch import
- 支持启动时自动安装依赖，降低首次使用门槛
- Installs dependencies automatically on first launch

## 快速启动 / Quick Start

### macOS

双击 `启动中转工具.command`。

Double-click `启动中转工具.command`.

### Windows

双击 `启动中转工具.bat`。

Double-click `启动中转工具.bat`.

启动脚本会自动完成以下操作：

The launcher scripts automatically:

1. 创建 `src/.venv` / Create `src/.venv`
2. 安装 `src/requirements.txt` 中的依赖 / Install dependencies from `src/requirements.txt`
3. 启动桌面 GUI / Start the desktop GUI

首次运行需要联网安装依赖。

The first launch requires network access to install dependencies.

## GUI 功能 / GUI Capabilities

- 配置上游 Base URL、模型名和 API Key
- Configure upstream Base URL, model name, and API key
- 启动或停止本地中转服务
- Start or stop the local adapter service
- 测试 DeepSeek 上游是否连通
- Test upstream DeepSeek connectivity
- 一键唤起 CC Switch 导入
- Trigger CC Switch import with one click
- 直接写入 Codex 配置
- Apply Codex configuration directly

默认上游配置 / Default upstream settings:

- Base URL: `https://api.deepseek.com`
- Path: `/chat/completions`
- Model: `deepseek-v4-pro`

## 对外接口 / API Endpoints

- `GET /health`
- `GET /v1/models`
- `POST /v1/responses`
- `POST /v1/chat/completions`

其中 `/v1/responses` 是主要入口。

`/v1/responses` is the main entry point.

## 项目结构 / Project Layout

```text
启动中转工具.command    macOS 启动脚本 / macOS launcher
启动中转工具.bat        Windows 启动脚本 / Windows launcher
src/                    源码与虚拟环境目录 / source code and virtual environment
tests/                  单元测试 / unit tests
build/                  打包配置 / build configs
```

## 开发说明 / Development

### 本地运行 GUI / Run the GUI locally

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

### 运行测试 / Run tests

推荐使用项目虚拟环境执行。

Using the project virtual environment is recommended.

macOS:

```bash
src/.venv/bin/python -m unittest discover -s tests -v
```

Windows:

```powershell
src\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 说明 / Notes

- DeepSeek 当前主要兼容 `chat/completions`，本项目负责把 `responses` 调用做适配转换
- DeepSeek currently mainly supports `chat/completions`, and this project adapts `responses` calls to that interface
- CC Switch 导入通过官方 deeplink 完成，不直接改写其数据库
- CC Switch integration uses the official deeplink flow instead of editing its database directly
- GUI 配置文件位于 `src/window_config.json`
- GUI runtime config is stored at `src/window_config.json`
