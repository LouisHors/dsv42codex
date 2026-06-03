from __future__ import annotations

import json
import os
from pathlib import Path
import queue
import socket
import sys
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

import httpx
from typing import Callable
import uvicorn

from ds_adapter.app import create_app
from ds_adapter.config import Settings
from ds_adapter.defaults import (
    DEFAULT_DEEPSEEK_BASE_URL,
    DEFAULT_DEEPSEEK_MODEL,
    DEEPSEEK_MODEL_OPTIONS,
)
import platform

from ds_adapter.integration import (
    FIXED_CHAT_PATH,
    FIXED_HOST,
    FIXED_MODEL_OWNER,
    FIXED_PORT,
    FIXED_STREAM_CHUNK_SIZE,
    FIXED_TIMEOUT_SECONDS,
    apply_codex_config,
    adapter_root_url,
    adapter_v1_url,
    build_cc_provider_deeplink,
    detect_codex_config_path,
    get_cc_codex_status,
    launch_cc_provider_import,
)


WORKSPACE = Path(__file__).resolve().parent
CONFIG_PATH = WORKSPACE / "window_config.json"
INSTANCE_HOST = "127.0.0.1"
INSTANCE_PORT = 19468
APP_NAME = "DSV4本地中转工具"
APP_VERSION = "1.0"
APP_TITLE = f"{APP_NAME}{APP_VERSION}"

_platform = platform.system()
if _platform == "Darwin":
    UI_FONT = "PingFang SC"
    MONO_FONT = "Menlo"
elif _platform == "Windows":
    UI_FONT = "Microsoft YaHei UI"
    MONO_FONT = "Consolas"
else:
    UI_FONT = "sans-serif"
    MONO_FONT = "monospace"

TEXT = {
    "title": APP_TITLE,
    "ready": "\u7a97\u53e3\u5df2\u5c31\u7eea\u3002\u9ed8\u8ba4\u672c\u5730\u5730\u5740\u56fa\u5b9a\u4e3a ",
    "default_status": "\u672a\u542f\u52a8",
    "upstream_url": "\u4e0a\u6e38 Base URL",
    "upstream_model": "\u4e0a\u6e38\u6a21\u578b\u540d",
    "api_key": "\u4e0a\u6e38 API Key\uff08\u5bfc\u5165 CC \u65f6\u5fc5\u586b\uff09",
    "test_prompt": "\u4e0a\u6e38\u76f4\u8fde\u6d4b\u8bd5\u63d0\u793a\u8bcd",
    "cc_import_row": "CC Switch \u4e00\u952e\u5bfc\u5165",
    "cc_import_sub": "\u901a\u8fc7 CC \u5b98\u65b9 ccswitch:// \u63a5\u53e3\u5524\u8d77\u5bfc\u5165\uff0c\u4e0d\u76f4\u63a5\u4fee\u6539 CC \u914d\u7f6e\u6587\u4ef6\u6216\u6570\u636e\u5e93\u3002",
    "cc_status": "CC \u5f53\u524d\u63a5\u7ba1\u72b6\u6001",
    "codex_config": "Codex \u914d\u7f6e\u8def\u5f84",
    "select": "\u9009\u62e9",
    "refresh_cc_status": "\u5237\u65b0 CC \u72b6\u6001",
    "save": "\u4fdd\u5b58\u914d\u7f6e",
    "start": "\u542f\u52a8\u670d\u52a1",
    "stop": "\u505c\u6b62\u670d\u52a1",
    "test_upstream": "\u6d4b\u8bd5\u4e0a\u6e38\u76f4\u8fde",
    "import_cc": "\u5bfc\u5165\u5230 CC",
    "apply_codex": "\u5e94\u7528 Codex \u914d\u7f6e",
    "open_browser": "\u6253\u5f00\u672c\u5730\u9875\u9762",
    "action_hint": "\u7a0b\u5e8f\u6253\u5f00\u540e\u4f1a\u81ea\u52a8\u542f\u52a8\u672c\u5730\u670d\u52a1\u3002\u201c\u6d4b\u8bd5\u4e0a\u6e38\u76f4\u8fde\u201d\u4f1a\u76f4\u63a5\u6d4b\u8bd5 DeepSeek \u4e0a\u6e38\u662f\u5426\u53ef\u7528\u3002\u201c\u5bfc\u5165\u5230 CC\u201d\u4f1a\u7528 CC \u5b98\u65b9 deeplink \u6253\u5f00\u5bfc\u5165\u5f39\u7a97\uff0c\u5e76\u628a\u5f53\u524d\u4e0a\u6e38 API Key \u4e00\u8d77\u5e26\u8fdb CC Provider\uff0c\u4f60\u53ea\u9700\u5728 CC \u91cc\u518d\u786e\u8ba4\u4e00\u6b21\u3002\u201c\u5e94\u7528 Codex \u914d\u7f6e\u201d\u4f1a\u76f4\u63a5\u5199\u5165 Codex \u914d\u7f6e\u6587\u4ef6\u3002",
    "log_title": "\u8fd0\u884c\u65e5\u5fd7",
    "log_sub": f"\u56fa\u5b9a\u672c\u5730\u5730\u5740\uff1a{adapter_v1_url()}  |  chat path \u56fa\u5b9a\u4e3a {FIXED_CHAT_PATH}",
    "save_ok": "\u914d\u7f6e\u5df2\u4fdd\u5b58\u5230 ",
    "save_failed": "\u4fdd\u5b58\u5931\u8d25",
    "start_failed": "\u542f\u52a8\u5931\u8d25",
    "missing_upstream": "\u7f3a\u5c11\u4e0a\u6e38\u5730\u5740",
    "running": "\u8fd0\u884c\u4e2d: ",
    "starting": "\u6b63\u5728\u542f\u52a8\u670d\u52a1: ",
    "already_running": "\u670d\u52a1\u5df2\u7ecf\u5728\u8fd0\u884c\u4e86\u3002",
    "stopped": "\u670d\u52a1\u5df2\u505c\u6b62\u3002",
    "no_service": "\u5f53\u524d\u6ca1\u6709\u8fd0\u884c\u4e2d\u7684\u670d\u52a1\u3002",
    "open_browser_log": "\u5df2\u5c1d\u8bd5\u6253\u5f00\u6d4f\u89c8\u5668: ",
    "service_not_started": "\u670d\u52a1\u672a\u542f\u52a8",
    "start_first": "\u8bf7\u5148\u542f\u52a8\u670d\u52a1\uff0c\u518d\u8fdb\u884c\u6d4b\u8bd5\u3002",
    "select_codex_title": "\u9009\u62e9 Codex \u914d\u7f6e\u6587\u4ef6",
    "cc_import_done": "\u5bfc\u5165\u5b8c\u6210",
    "cc_import_done_msg": "\u5df2\u5524\u8d77 CC Switch\uff0c\u8bf7\u5728 CC \u5f39\u7a97\u91cc\u786e\u8ba4\u5bfc\u5165\u3002\u5bfc\u5165\u94fe\u63a5\u4e5f\u5df2\u590d\u5236\u5230\u526a\u8d34\u677f\u3002",
    "cc_import_done_msg_no_clipboard": "\u5df2\u5524\u8d77 CC Switch\uff0c\u8bf7\u5728 CC \u5f39\u7a97\u91cc\u786e\u8ba4\u5bfc\u5165\u3002",
    "cc_import_failed_clipboard": "\u81ea\u52a8\u5524\u8d77\u5931\u8d25\uff0c\u4f46\u5bfc\u5165\u94fe\u63a5\u5df2\u590d\u5236\u5230\u526a\u8d34\u677f\uff0c\u53ef\u4ee5\u624b\u52a8\u7c98\u8d34\u5230\u8fd0\u884c\u7a97\u53e3\u6216\u6d4f\u89c8\u5668\u5730\u5740\u680f\u3002",
    "cc_import_failed": "\u5bfc\u5165\u5931\u8d25",
    "cc_import_key_required": "\u5bfc\u5165\u5230 CC \u524d\uff0c\u8bf7\u5148\u586b\u5199\u4e0a\u6e38 API Key\u3002CC \u4f1a\u6821\u9a8c Codex Provider \u7684 key\uff0c\u800c\u672c\u5730\u9002\u914d\u5c42\u4e5f\u53ef\u4ee5\u7528\u5b83\u8f6c\u53d1\u5230 DeepSeek\u3002",
    "cc_status_ok": "CC \u5df2\u5207\u5230\u672c\u5730\u4e2d\u8f6c\u3002",
    "cc_status_warn": "CC \u5c1a\u672a\u5207\u5230\u672c\u5730\u4e2d\u8f6c\u3002",
    "codex_apply_ok": "\u5e94\u7528\u6210\u529f",
    "codex_apply_ok_msg": "Codex \u914d\u7f6e\u5df2\u6b63\u5f0f\u5199\u5165\u3002",
    "codex_apply_warn": "\u5e94\u7528\u672a\u901a\u8fc7",
    "upstream_test_ok": "\u4e0a\u6e38\u76f4\u8fde\u5df2\u901a",
    "upstream_test_failed": "\u4e0a\u6e38\u76f4\u8fde\u5931\u8d25",
    "upstream_test_running": "\u6b63\u5728\u6d4b\u8bd5\u4e0a\u6e38\u76f4\u8fde...",
    "upstream_test_empty": "\u6d4b\u8bd5\u5df2\u8fd4\u56de\uff0c\u4f46\u6ca1\u6709\u89e3\u6790\u5230\u53ef\u8bfb\u56de\u590d\u5185\u5bb9\u3002",
    "proc_exit": "\u670d\u52a1\u8fdb\u7a0b\u5df2\u9000\u51fa\uff0c\u8fd4\u56de\u7801: ",
    "exited": "\u5df2\u9000\u51fa",
    "auto_starting": "\u7a0b\u5e8f\u542f\u52a8\u540e\u6b63\u5728\u81ea\u52a8\u542f\u52a8\u670d\u52a1...",
    "auto_started": "\u5df2\u81ea\u52a8\u542f\u52a8\u672c\u5730\u670d\u52a1\u3002",
    "service_ready": "\u672c\u5730\u670d\u52a1\u5df2\u5c31\u7eea: ",
    "service_external": "\u68c0\u6d4b\u5230\u5df2\u6709\u672c\u5730\u670d\u52a1\u5728\u8fd0\u884c: ",
    "stop_external_denied": "\u5f53\u524d\u670d\u52a1\u4e0d\u662f\u7531\u672c\u7a97\u53e3\u542f\u52a8\u7684\uff0c\u4e0d\u63d0\u4f9b\u505c\u6b62\u3002",
}


class AdapterWindow:
    def __init__(self, root: tk.Tk, instance_server: socket.socket | None = None) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("980x760")
        self.root.minsize(900, 700)

        self.instance_server = instance_server
        self.instance_listener_thread: threading.Thread | None = None
        self.server: uvicorn.Server | None = None
        self.server_thread: threading.Thread | None = None
        self.server_app = None
        self.log_queue: queue.Queue[str] = queue.Queue()

        self.upstream_base_url_var = tk.StringVar(value=DEFAULT_DEEPSEEK_BASE_URL)
        self.upstream_model_var = tk.StringVar(value=DEFAULT_DEEPSEEK_MODEL)
        self.api_key_var = tk.StringVar(value="")
        self.codex_config_path_var = tk.StringVar(value=str(detect_codex_config_path()))
        self.test_prompt_var = tk.StringVar(value="\u8bf7\u56de\u590d ok")
        self.status_var = tk.StringVar(value=TEXT["default_status"])
        self.cc_status_var = tk.StringVar(value="\u6b63\u5728\u68c0\u67e5 CC \u5f53\u524d\u63a5\u7ba1\u72b6\u6001...")
        self._load_config()
        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self._start_instance_listener()
        self.root.after(200, self._flush_logs)
        self.root.after(500, self._poll_process)
        self.root.after(700, self.ensure_server_running)

    def _build_ui(self) -> None:
        self.root.configure(bg="#efe7dc")

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Card.TFrame", background="#fffdf8")
        style.configure("Accent.TButton", padding=(16, 10), font=(UI_FONT, 10, "bold"))
        style.configure("TButton", padding=(12, 10), font=(UI_FONT, 10))
        style.configure("TLabel", background="#fffdf8", foreground="#1f2937", font=(UI_FONT, 10))
        style.configure("Header.TLabel", background="#fffdf8", foreground="#111827", font=(UI_FONT, 18, "bold"))
        style.configure("Muted.TLabel", background="#fffdf8", foreground="#5b6472", font=(UI_FONT, 10))

        outer = ttk.Frame(self.root, style="Card.TFrame", padding=18)
        outer.pack(fill="both", expand=True, padx=18, pady=18)

        log_card = ttk.Frame(outer, style="Card.TFrame", padding=18)
        log_card.pack(fill="both", pady=(0, 12))
        ttk.Label(log_card, text=TEXT["log_title"], style="Header.TLabel").pack(anchor="w")
        ttk.Label(log_card, text=TEXT["log_sub"], style="Muted.TLabel").pack(anchor="w", pady=(4, 10))

        self.log_text = tk.Text(
            log_card,
            wrap="word",
            height=13,
            font=(MONO_FONT, 10),
            bg="#17212b",
            fg="#ecf4ff",
            insertbackground="#ecf4ff",
            relief="flat",
            padx=14,
            pady=14,
        )
        self.log_text.pack(fill="both", expand=True)

        form_card = ttk.Frame(outer, style="Card.TFrame", padding=18)
        form_card.pack(fill="x", pady=(0, 12))
        form_card.columnconfigure(0, weight=1)
        form_card.columnconfigure(1, weight=1)

        self._field(form_card, TEXT["upstream_url"], self.upstream_base_url_var, 0, 0)
        self._combo_field(
            form_card,
            TEXT["upstream_model"],
            self.upstream_model_var,
            DEEPSEEK_MODEL_OPTIONS,
            0,
            1,
            on_selected=self.on_upstream_model_selected,
        )
        self._field(form_card, TEXT["api_key"], self.api_key_var, 1, 0, show="*")
        self._field_with_button(form_card, TEXT["test_prompt"], self.test_prompt_var, TEXT["test_upstream"], self.test_upstream, 1, 1)

        path_card = ttk.Frame(outer, style="Card.TFrame", padding=18)
        path_card.pack(fill="x", pady=(0, 12))
        path_card.columnconfigure(1, weight=1)

        ttk.Label(path_card, text=TEXT["cc_import_row"]).grid(row=0, column=0, sticky="w")
        ttk.Label(path_card, text=TEXT["cc_import_sub"], style="Muted.TLabel").grid(row=0, column=1, sticky="w", padx=(12, 8))
        ttk.Button(path_card, text=TEXT["import_cc"], command=self.import_to_cc, style="Accent.TButton").grid(row=0, column=2, sticky="e")

        ttk.Label(path_card, text=TEXT["cc_status"]).grid(row=1, column=0, sticky="w", pady=(12, 0))
        ttk.Label(path_card, textvariable=self.cc_status_var, style="Muted.TLabel").grid(row=1, column=1, sticky="w", padx=(12, 8), pady=(12, 0))
        ttk.Button(path_card, text=TEXT["refresh_cc_status"], command=self.refresh_cc_status).grid(row=1, column=2, sticky="e", pady=(12, 0))

        ttk.Label(path_card, text=TEXT["codex_config"]).grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(path_card, textvariable=self.codex_config_path_var).grid(row=2, column=1, sticky="ew", padx=(12, 8), pady=(12, 0))
        ttk.Button(path_card, text=TEXT["select"], command=self.choose_codex_config).grid(row=2, column=2, sticky="e", pady=(12, 0))
        ttk.Button(path_card, text=TEXT["apply_codex"], command=self.apply_codex_import, style="Accent.TButton").grid(row=2, column=3, sticky="e", padx=(8, 0), pady=(12, 0))

        action_card = ttk.Frame(outer, style="Card.TFrame", padding=18)
        action_card.pack(fill="x", pady=(0, 12))
        ttk.Label(action_card, textvariable=self.status_var, style="Muted.TLabel").pack(anchor="w")

        row1 = ttk.Frame(action_card, style="Card.TFrame")
        row1.pack(fill="x", pady=(12, 0))
        ttk.Button(row1, text=TEXT["save"], command=self.save_config).pack(side="left")
        ttk.Button(row1, text=TEXT["start"], command=self.start_server, style="Accent.TButton").pack(side="left", padx=(10, 0))
        ttk.Button(row1, text=TEXT["stop"], command=self.stop_server).pack(side="left", padx=(10, 0))
        ttk.Button(row1, text=TEXT["open_browser"], command=self.open_browser).pack(side="left", padx=(10, 0))

        ttk.Label(action_card, text=TEXT["action_hint"], style="Muted.TLabel").pack(anchor="w", pady=(12, 0))

        self.log(TEXT["ready"] + adapter_v1_url())
        self.root.after(300, self.refresh_cc_status)

    def _field(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        row: int,
        column: int,
        show: str | None = None,
        colspan: int = 1,
    ) -> None:
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, columnspan=colspan, sticky="ew", padx=(0 if column == 0 else 8), pady=8)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label).grid(row=0, column=0, sticky="w")
        ttk.Entry(frame, textvariable=variable, show=show or "").grid(row=1, column=0, sticky="ew", pady=(6, 0))

    def _combo_field(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        values: tuple[str, ...],
        row: int,
        column: int,
        on_selected=None,
    ) -> None:
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, sticky="ew", padx=(0 if column == 0 else 8), pady=8)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label).grid(row=0, column=0, sticky="w")
        combo = ttk.Combobox(frame, textvariable=variable, values=list(values), state="readonly")
        combo.grid(row=1, column=0, sticky="ew", pady=(6, 0))
        if on_selected is not None:
            combo.bind("<<ComboboxSelected>>", on_selected)

    def _field_with_button(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        button_text: str,
        command,
        row: int,
        column: int,
        colspan: int = 1,
        show: str | None = None,
    ) -> None:
        frame = ttk.Frame(parent, style="Card.TFrame")
        frame.grid(row=row, column=column, columnspan=colspan, sticky="ew", padx=(0 if column == 0 else 8), pady=8)
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text=label).grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Entry(frame, textvariable=variable, show=show or "").grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Button(frame, text=button_text, command=command).grid(row=1, column=1, sticky="e", padx=(10, 0), pady=(6, 0))

    def current_config(self) -> dict[str, str]:
        return {
            "upstream_base_url": self.upstream_base_url_var.get().strip(),
            "upstream_model": self.upstream_model_var.get().strip() or DEFAULT_DEEPSEEK_MODEL,
            "upstream_api_key": self.api_key_var.get(),
            "codex_config_path": self.codex_config_path_var.get().strip(),
            "test_prompt": self.test_prompt_var.get().strip() or "\u8bf7\u56de\u590d ok",
        }

    def persisted_config(self) -> dict[str, str]:
        return self.current_config().copy()

    def _load_config(self) -> None:
        if not CONFIG_PATH.exists():
            return
        try:
            payload = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            return
        self.upstream_base_url_var.set(str(payload.get("upstream_base_url") or self.upstream_base_url_var.get()))
        self.upstream_model_var.set(str(payload.get("upstream_model") or self.upstream_model_var.get()))
        self.api_key_var.set(str(payload.get("upstream_api_key") or self.api_key_var.get()))
        self.codex_config_path_var.set(str(payload.get("codex_config_path") or self.codex_config_path_var.get()))
        self.test_prompt_var.set(str(payload.get("test_prompt") or self.test_prompt_var.get()))

    def save_config(self, silent: bool = False) -> bool:
        try:
            CONFIG_PATH.write_text(json.dumps(self.persisted_config(), ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as exc:
            if not silent:
                messagebox.showerror(TEXT["save_failed"], f"{TEXT['save_failed']}\uff1a{exc}")
            self.log(f"{TEXT['save_failed']}: {exc}")
            return False
        if not silent:
            self.log(TEXT["save_ok"] + str(CONFIG_PATH))
        return True

    def on_upstream_model_selected(self, _event=None) -> None:
        model_name = self.upstream_model_var.get().strip() or DEFAULT_DEEPSEEK_MODEL
        self.save_config(silent=True)
        pushed = self.push_config_to_running_service(silent=True)
        if pushed:
            self.status_var.set(TEXT["service_ready"] + adapter_v1_url())
            self.log(f"\u5df2\u81ea\u52a8\u5207\u6362\u4e0a\u6e38\u6a21\u578b\u5230: {model_name}")
        else:
            self.log(f"\u5df2\u4fdd\u5b58\u4e0a\u6e38\u6a21\u578b\uff0c\u5f85\u670d\u52a1\u4f7f\u7528: {model_name}")

    def _start_instance_listener(self) -> None:
        if self.instance_server is None:
            return
        self.instance_listener_thread = threading.Thread(target=self._listen_for_instance_messages, daemon=True)
        self.instance_listener_thread.start()

    def _listen_for_instance_messages(self) -> None:
        assert self.instance_server is not None
        while True:
            try:
                conn, _ = self.instance_server.accept()
            except OSError:
                return
            with conn:
                try:
                    message = conn.recv(64).decode("utf-8", errors="ignore").strip().upper()
                except OSError:
                    continue
            if message == "SHOW":
                self.root.after(0, self.bring_to_front)

    def build_server_env(self) -> dict[str, str]:
        config = self.current_config()
        final_env = os.environ.copy()
        final_env["UPSTREAM_BASE_URL"] = config["upstream_base_url"]
        final_env["UPSTREAM_CHAT_PATH"] = FIXED_CHAT_PATH
        final_env["UPSTREAM_MODEL"] = config["upstream_model"]
        final_env["ADAPTER_MODEL_IDS"] = config["upstream_model"]
        final_env["MODEL_OWNER"] = FIXED_MODEL_OWNER
        final_env["UPSTREAM_TIMEOUT_SECONDS"] = str(FIXED_TIMEOUT_SECONDS)
        final_env["STREAM_CHUNK_SIZE"] = str(FIXED_STREAM_CHUNK_SIZE)
        final_env["FORWARD_AUTHORIZATION"] = "true"
        if config["upstream_api_key"].strip():
            final_env["UPSTREAM_API_KEY"] = config["upstream_api_key"]
        else:
            final_env.pop("UPSTREAM_API_KEY", None)
        return final_env

    def build_server_settings(self) -> Settings:
        config = self.current_config()
        return Settings(
            upstream_base_url=config["upstream_base_url"] or DEFAULT_DEEPSEEK_BASE_URL,
            upstream_chat_path=FIXED_CHAT_PATH,
            upstream_api_key=config["upstream_api_key"].strip() or None,
            adapter_model_ids=(config["upstream_model"],),
            upstream_model=config["upstream_model"],
            request_timeout_seconds=float(FIXED_TIMEOUT_SECONDS),
            synthesize_stream_chunk_size=int(FIXED_STREAM_CHUNK_SIZE),
            forward_authorization=True,
            model_owner=FIXED_MODEL_OWNER,
        )

    def start_server(self, auto: bool = False) -> bool:
        if self.server_thread and self.server_thread.is_alive() and self.server is not None:
            self.log(TEXT["already_running"])
            self.status_var.set(TEXT["running"] + adapter_v1_url())
            self.push_config_to_running_service(silent=True)
            return True

        if self.is_service_available():
            self.push_config_to_running_service(silent=True)
            self.status_var.set(TEXT["service_external"] + adapter_v1_url())
            self.log(TEXT["service_external"] + adapter_v1_url())
            return True

        config = self.current_config()
        if not config["upstream_base_url"]:
            if not auto:
                messagebox.showwarning(TEXT["missing_upstream"], "\u8bf7\u5148\u586b\u5199\u4e0a\u6e38 Base URL\u3002")
            return False

        self.save_config()
        try:
            self.server_app = create_app(settings=self.build_server_settings())
            config_obj = uvicorn.Config(
                self.server_app,
                host=FIXED_HOST,
                port=FIXED_PORT,
                log_level="warning",
                access_log=False,
                use_colors=False,
                log_config=None,
            )
            self.server = uvicorn.Server(config_obj)
            self.server_thread = threading.Thread(target=self.server.run, daemon=True)
            self.server_thread.start()
        except Exception as exc:
            if not auto:
                messagebox.showerror(TEXT["start_failed"], f"{TEXT['start_failed']}\uff1a{exc}")
            self.log(f"{TEXT['start_failed']}: {exc}")
            return False

        self.log(TEXT["starting"] + adapter_v1_url())
        for _ in range(30):
            if self.is_service_available():
                self.status_var.set(TEXT["running"] + adapter_v1_url())
                self.push_config_to_running_service(silent=True)
                return True
            time.sleep(0.1)

        self.server = None
        self.server_thread = None
        self.server_app = None
        self.log(f"{TEXT['start_failed']}: \u672c\u5730\u670d\u52a1\u5728\u9884\u671f\u65f6\u95f4\u5185\u672a\u5c31\u7eea")
        return False

    def ensure_server_running(self) -> None:
        if self.server_thread and self.server_thread.is_alive():
            self.status_var.set(TEXT["service_ready"] + adapter_v1_url())
            return
        if self.is_service_available():
            self.status_var.set(TEXT["service_external"] + adapter_v1_url())
            self.log(TEXT["service_external"] + adapter_v1_url())
            return
        self.log(TEXT["auto_starting"])
        if self.start_server(auto=True):
            self.log(TEXT["auto_started"])

    def stop_server(self) -> None:
        if self.server is None and self.is_service_available():
            self.log(TEXT["stop_external_denied"])
            return
        if self.server is None or self.server_thread is None:
            self.status_var.set(TEXT["default_status"])
            self.log(TEXT["no_service"])
            return
        self.server.should_exit = True
        self.server_thread.join(timeout=5)
        if self.server_thread.is_alive():
            self.log(f"{TEXT['stopped']} (\u5f3a\u5236\u9000\u51fa\u8d85\u65f6)")
        self.log(TEXT["stopped"])
        self.status_var.set(TEXT["default_status"])
        self.server = None
        self.server_thread = None
        self.server_app = None

    def choose_codex_config(self) -> None:
        selected = filedialog.askopenfilename(
            title=TEXT["select_codex_title"],
            filetypes=[("TOML", "*.toml"), ("All files", "*.*")],
        )
        if selected:
            self.codex_config_path_var.set(selected)
            self.log(f"{TEXT['codex_config']}: {selected}")

    def open_browser(self) -> None:
        url = adapter_root_url()
        webbrowser.open(url)
        self.log(TEXT["open_browser_log"] + url)

    def test_upstream(self) -> None:
        self.status_var.set(TEXT["upstream_test_running"])
        self._run_http_action(
            TEXT["test_upstream"],
            "/admin/test-upstream",
            {
                "upstream_base_url": self.upstream_base_url_var.get().strip(),
                "upstream_chat_path": FIXED_CHAT_PATH,
                "upstream_model": self.upstream_model_var.get().strip() or DEFAULT_DEEPSEEK_MODEL,
                "adapter_model_ids": self.upstream_model_var.get().strip() or DEFAULT_DEEPSEEK_MODEL,
                "upstream_api_key": self.api_key_var.get(),
                "model_owner": FIXED_MODEL_OWNER,
                "request_timeout_seconds": FIXED_TIMEOUT_SECONDS,
                "synthesize_stream_chunk_size": FIXED_STREAM_CHUNK_SIZE,
                "forward_authorization": True,
                "prompt": self.test_prompt_var.get().strip() or "\u8bf7\u56de\u590d ok",
            },
            on_complete=self._handle_upstream_test_result,
        )

    def import_to_cc(self) -> None:
        adapter_model = self.upstream_model_var.get().strip() or DEFAULT_DEEPSEEK_MODEL
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning(TEXT["cc_import_failed"], TEXT["cc_import_key_required"])
            self.log(TEXT["cc_import_key_required"])
            return
        deeplink = build_cc_provider_deeplink(adapter_model, api_key)
        clipboard_ok = self._copy_to_clipboard(deeplink)
        try:
            result = launch_cc_provider_import(adapter_model, api_key)
        except Exception as exc:
            messagebox.showerror(TEXT["cc_import_failed"], f"{TEXT['cc_import_failed']}\uff1a{exc}")
            self.log(f"{TEXT['cc_import_failed']}: {exc}")
            return

        result["clipboard_copied"] = clipboard_ok
        self.log(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("ok"):
            self.refresh_cc_status()
            message = TEXT["cc_import_done_msg"] if clipboard_ok else TEXT["cc_import_done_msg_no_clipboard"]
            messagebox.showinfo(TEXT["cc_import_done"], message)
            return

        detail = str(result.get("message") or TEXT["cc_import_failed"])
        if clipboard_ok:
            detail = f"{detail}\n\n{TEXT['cc_import_failed_clipboard']}"
        messagebox.showerror(TEXT["cc_import_failed"], detail)

    def apply_codex_import(self) -> None:
        config_path = Path(self.codex_config_path_var.get().strip())
        result = apply_codex_config(config_path, self.upstream_model_var.get().strip() or DEFAULT_DEEPSEEK_MODEL)
        self.log(json.dumps(result, ensure_ascii=False, indent=2))
        if result.get("ok"):
            messagebox.showinfo(TEXT["codex_apply_ok"], TEXT["codex_apply_ok_msg"])
        else:
            messagebox.showwarning(TEXT["codex_apply_warn"], str(result.get("message") or "\u5e94\u7528\u5931\u8d25\u3002"))

    def refresh_cc_status(self) -> None:
        try:
            result = get_cc_codex_status()
        except Exception as exc:
            detail = f"\u8bfb\u53d6 CC \u72b6\u6001\u5931\u8d25: {exc}"
            self.cc_status_var.set(detail)
            self.log(detail)
            return

        message = str(result.get("message") or "\u672a\u83b7\u53d6\u5230 CC \u72b6\u6001\u3002")
        self.cc_status_var.set(message)
        if result.get("ok"):
            self.log(TEXT["cc_status_ok"] + " " + message)
        else:
            self.log(TEXT["cc_status_warn"] + " " + message)

    def _run_http_action(
        self,
        label: str,
        path: str,
        payload: dict[str, object],
        on_complete: Callable[[bool, int | None, str], None] | None = None,
    ) -> None:
        if not self.is_service_available():
            messagebox.showwarning(TEXT["service_not_started"], TEXT["start_first"])
            self.log(f"{label}: {TEXT['service_not_started']}")
            return

        def worker() -> None:
            url = f"{adapter_root_url()}{path}"
            try:
                with httpx.Client(timeout=20) as client:
                    response = client.post(url, json=payload)
                    body = response.text
                self.log_queue.put(f"{label} -> {response.status_code}\n{body}")
                if on_complete is not None:
                    self.root.after(0, lambda: on_complete(response.status_code < 400, response.status_code, body))
            except Exception as exc:
                self.log_queue.put(f"{label}: {exc}")
                if on_complete is not None:
                    self.root.after(0, lambda: on_complete(False, None, str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.log(label + "...")

    def push_config_to_running_service(self, silent: bool = False) -> bool:
        if not self.is_service_available():
            return False
        payload = {
            "upstream_base_url": self.upstream_base_url_var.get().strip(),
            "upstream_chat_path": FIXED_CHAT_PATH,
            "upstream_model": self.upstream_model_var.get().strip() or DEFAULT_DEEPSEEK_MODEL,
            "adapter_model_ids": self.upstream_model_var.get().strip() or DEFAULT_DEEPSEEK_MODEL,
            "upstream_api_key": self.api_key_var.get(),
            "model_owner": FIXED_MODEL_OWNER,
            "request_timeout_seconds": FIXED_TIMEOUT_SECONDS,
            "synthesize_stream_chunk_size": FIXED_STREAM_CHUNK_SIZE,
            "forward_authorization": True,
        }
        try:
            response = httpx.post(f"{adapter_root_url()}/admin/config", json=payload, timeout=10)
            response.raise_for_status()
        except Exception as exc:
            if not silent:
                self.log(f"\u540c\u6b65\u8fd0\u884c\u914d\u7f6e\u5931\u8d25: {exc}")
            return False
        if not silent:
            self.log("\u5df2\u540c\u6b65\u914d\u7f6e\u5230\u8fd0\u884c\u4e2d\u670d\u52a1\u3002")
        return True

    def _handle_upstream_test_result(self, ok: bool, status_code: int | None, body: str) -> None:
        if ok:
            self.status_var.set(TEXT["service_ready"] + adapter_v1_url())
            preview_text = TEXT["upstream_test_empty"]
            try:
                payload = json.loads(body)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                preview = payload.get("upstream_preview")
                if isinstance(preview, dict):
                    choices = preview.get("choices")
                    if isinstance(choices, list) and choices:
                        message = choices[0].get("message")
                        if isinstance(message, dict):
                            content = str(message.get("content") or "").strip()
                            if content:
                                preview_text = content[:220]
            messagebox.showinfo(TEXT["upstream_test_ok"], preview_text)
            return

        detail = body.strip() or (f"HTTP {status_code}" if status_code is not None else "\u672a\u77e5\u9519\u8bef")
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict):
            error = payload.get("error")
            if isinstance(error, dict):
                parsed_message = str(error.get("message") or "").strip()
                if parsed_message:
                    detail = parsed_message
        self.status_var.set(TEXT["upstream_test_failed"])
        messagebox.showerror(TEXT["upstream_test_failed"], detail)

    def _poll_process(self) -> None:
        if self.server is not None and self.server_thread is not None and not self.server_thread.is_alive():
            self.log(TEXT["proc_exit"] + "embedded")
            if self.is_service_available():
                self.status_var.set(TEXT["service_external"] + adapter_v1_url())
            else:
                self.status_var.set(TEXT["exited"])
            self.server = None
            self.server_thread = None
            self.server_app = None
        self.root.after(500, self._poll_process)

    def _flush_logs(self) -> None:
        while True:
            try:
                line = self.log_queue.get_nowait()
            except queue.Empty:
                break
            self.log(line)
        self.root.after(200, self._flush_logs)

    def log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def _copy_to_clipboard(self, text: str) -> bool:
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
        except tk.TclError:
            return False
        return True

    def is_service_available(self) -> bool:
        try:
            response = httpx.get(f"{adapter_root_url()}/health", timeout=1.5)
        except Exception:
            return False
        return response.status_code == 200

    def bring_to_front(self) -> None:
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.after(200, lambda: self.root.attributes("-topmost", False))
            self.root.focus_force()
        except tk.TclError:
            pass

    def on_close(self) -> None:
        if self.server is not None and self.server_thread is not None and self.server_thread.is_alive():
            self.stop_server()
        if self.instance_server is not None:
            try:
                self.instance_server.close()
            except OSError:
                pass
        self.root.destroy()


def acquire_single_instance_server() -> socket.socket | None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
        server.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        server.bind((INSTANCE_HOST, INSTANCE_PORT))
    except OSError:
        server.close()
        return None
    server.listen(1)
    return server


def notify_existing_instance() -> bool:
    try:
        with socket.create_connection((INSTANCE_HOST, INSTANCE_PORT), timeout=1.0) as conn:
            conn.sendall(b"SHOW\n")
        return True
    except OSError:
        return False


def main() -> None:
    instance_server = acquire_single_instance_server()
    if instance_server is None:
        if notify_existing_instance():
            return
        instance_server = acquire_single_instance_server()
        if instance_server is None:
            return

    root = tk.Tk()
    AdapterWindow(root, instance_server=instance_server)
    root.mainloop()


if __name__ == "__main__":
    main()
