import json
import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox

import urllib.request
import urllib.error

from TRATA.block_window import BlockWindow
from TRATA.password_window import PasswordWindow

# CONFIG.
BASE_URL = "http://127.0.0.1:5000"

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".cyber_resilience")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
WINDOW_SCALE = 1.25


def center_window(window, width: int, height: int) -> None:
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def center_window(window, width: int, height: int) -> None:
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


# ---------------------------------------------------------------------------
# Local storage helpers
# ---------------------------------------------------------------------------

def load_local_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        return {}
    try:
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_local_config(data: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    # TODO: replace with keyring.set_password("cyber_resilience", "api_key", key)
    # before this goes anywhere near a real deployment. Plaintext json is a
    # hackathon shortcut only.
    existing = load_local_config()
    existing.update(data)
    with open(CONFIG_PATH, "w") as f:
        json.dump(existing, f, indent=2)


# ---------------------------------------------------------------------------
# Backend calls
# ---------------------------------------------------------------------------

def call_backend_json(url: str, method: str = "GET", body: dict | None = None,
                       api_key: str | None = None, timeout: int = 8) -> dict:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    data_bytes = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {"status": resp.status, "body": json.loads(resp.read().decode("utf-8"))}
    except urllib.error.HTTPError as e:
        try:
            return {"status": e.code, "body": json.loads(e.read().decode("utf-8"))}
        except Exception:
            return {"status": e.code, "body": {"error": str(e)}}
    except urllib.error.URLError as e:
        return {"status": None, "body": {"error": str(e)}}


def validate_api_key(api_key: str) -> dict:
    return call_backend_json(f"{BASE_URL}/api/auth/validate", method="POST", body={"api_key": api_key})


def fetch_agent_config(api_key: str) -> dict:
    return call_backend_json(f"{BASE_URL}/api/config", method="GET", api_key=api_key)

# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

class ApiKeyWindow(tk.Tk):
    def __init__(self, on_success=None):
        super().__init__()
        self.on_success = on_success  # callback(api_key: str, agent_config: dict)

        self.withdraw()
        self.tk.call("tk", "scaling", WINDOW_SCALE)
        self.title("Cyber Resilience Agent — Setup")
        center_window(self, 650, 390)
        self.resizable(False, False)
        self.deiconify()

        self._build_ui()
        self._prefill_saved_key()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 8}

        header = ttk.Label(self, text="Connect Agent", font=("Segoe UI", 14, "bold"), wraplength=400)
        header.pack(anchor="w", **pad)

        subtitle = ttk.Label(
            self,
            text="Enter the API key issued for this deployment to link\n"
                 "this agent with the Cyber Resilience backend.",
            foreground="#555555",
            justify="left",
            wraplength=400,
        )
        subtitle.pack(anchor="w", padx=20)

        form = ttk.Frame(self)
        form.pack(fill="x", **pad)

        ttk.Label(form, text="API Key:").grid(row=0, column=0, sticky="w")
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(form, textvariable=self.key_var, show="•", width=50)
        self.key_entry.grid(row=1, column=0, pady=(4, 0), sticky="we")
        self.key_entry.bind("<Return>", lambda event: self._on_connect_clicked())

        self.show_key_var = tk.BooleanVar(value=False)
        show_chk = ttk.Checkbutton(
            form, text="Show key", variable=self.show_key_var,
            command=self._toggle_key_visibility
        )
        show_chk.grid(row=1, column=1, padx=(8, 0))

        self.remember_var = tk.BooleanVar(value=True)
        remember_chk = ttk.Checkbutton(self, text="Remember this key on this machine",
                                        variable=self.remember_var)
        remember_chk.pack(anchor="w", padx=20)

        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground="#b00020", wraplength=400)
        self.status_label.pack(anchor="w", padx=20, pady=(4, 0))

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=20, pady=16)

        self.connect_btn = ttk.Button(btn_frame, text="Validate & Connect",
                                       command=self._on_connect_clicked)
        self.connect_btn.pack(side="right")

        self.progress = ttk.Progressbar(self, mode="indeterminate")
        # gridded/packed only while validating; hidden otherwise

    def _toggle_key_visibility(self):
        self.key_entry.config(show="" if self.show_key_var.get() else "•")

    def _prefill_saved_key(self):
        cfg = load_local_config()
        saved_key = cfg.get("api_key")
        if saved_key:
            self.key_var.set(saved_key)
            self.status_var.set("Found a saved key — re-validating automatically...")
            self.status_label.config(foreground="#555555")
            self.after(200, self._on_connect_clicked)

    # -- Connection flow ----------------------------------------------------

    def _on_connect_clicked(self):
        api_key = self.key_var.get().strip()
        if not api_key:
            self._set_status("Please enter an API key.", error=True)
            return

        self._set_busy(True)
        self._set_status("Validating key with backend...", error=False)

        thread = threading.Thread(target=self._validate_in_background, args=(api_key,), daemon=True)
        thread.start()

    def _validate_in_background(self, api_key: str):
        result = validate_api_key(api_key)
        # Hop back to the Tk main thread before touching any widgets
        self.after(0, lambda: self._handle_validation_result(api_key, result))

    def _handle_validation_result(self, api_key: str, result: dict):
        status, body = result["status"], result["body"]

        if status == 200 and body.get("valid"):
            org_name = body.get("org_name", "Unknown org")
            self._set_status(f"Connected — {org_name}", error=False)

            if self.remember_var.get():
                save_local_config({
                    "api_key": api_key,
                    "org_id": body.get("org_id"),
                    "org_name": org_name,
                    "agent_id": body.get("agent_id"),
                    "permissions": body.get("permissions", []),
                })

            # Pull agent config so the next window (Settings) opens pre-filled
            self._set_status(f"Connected — {org_name}. Fetching agent config...", error=False)
            thread = threading.Thread(target=self._fetch_config_in_background,
                                       args=(api_key, body), daemon=True)
            thread.start()

        elif status == 401 or (status == 200 and body.get("valid") is False):
            self._set_busy(False)
            self._set_status("Invalid API key. Please check and try again.", error=True)

        else:
            self._set_busy(False)
            err = body.get("error", "Unknown error")
            self._set_status(f"Could not reach backend ({err}).", error=True)

    def _fetch_config_in_background(self, api_key: str, validate_body: dict):
        cfg_result = fetch_agent_config(api_key)
        self.after(0, lambda: self._finish_connect(api_key, validate_body, cfg_result))

    def _finish_connect(self, api_key: str, validate_body: dict, cfg_result: dict):
        self._set_busy(False)
        agent_config = cfg_result["body"] if cfg_result["status"] == 200 else {}

        if self.on_success:
            self.destroy()
            self.on_success(api_key, {**validate_body, **agent_config})
        else:
            messagebox.showinfo("Connected", f"Linked to {validate_body.get('org_name')}.\n"
                                              f"(No follow-up window wired up yet.)")

    # -- UI helpers -----------------------------------------------------------

    def _set_busy(self, busy: bool):
        self.connect_btn.config(state="disabled" if busy else "normal")
        self.key_entry.config(state="disabled" if busy else "normal")
        if busy:
            self.progress.pack(fill="x", padx=20, pady=(0, 8))
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.pack_forget()

    def _set_status(self, msg: str, error: bool):
        self.status_var.set(msg)
        self.status_label.config(foreground="#b00020" if error else "#0a7d2c")


def create_main_window(on_success=None, blocking=False):
    if blocking:
        return BlockWindow(continue_to_api_key=False, next_callback=None)
    return BlockWindow(continue_to_api_key=True, next_callback=lambda: ApiKeyWindow(on_success=on_success).mainloop())


# ---------------------------------------------------------------------------
# Standalone run (swap the on_success callback for your real Settings window)
# ---------------------------------------------------------------------------

def _demo_on_success(api_key: str, agent_config: dict):
    print("Connected with key:", api_key[:6] + "..." if len(api_key) > 6 else api_key)
    print("Agent config received:", agent_config)
    messagebox.showinfo(
        "Connected",
        f"Org: {agent_config.get('org_name')}\n"
        f"Poll interval: {agent_config.get('poll_interval_minutes', '—')} min\n"
        f"PCAP dir: {agent_config.get('pcap_watch_dir', '—')}\n\n"
        "Next: hand off to the Settings window here."
    )


if __name__ == "__main__":

    def on_success(api_key: str, agent_config: dict):
        app = PasswordWindow(api_key=api_key, agent_config=agent_config)
        app.mainloop()

    app = create_main_window(on_success=on_success, blocking=True)  # swap it with settings window, jo khulegi on success.
    app.mainloop()