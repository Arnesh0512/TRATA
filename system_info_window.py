import json
import os
import tkinter as tk
import urllib.error
import urllib.request
from datetime import date, timedelta
from tkinter import filedialog, messagebox, ttk

BASE_URL = "https://trata-production.up.railway.app/agents"
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

DEFAULT_PCAP_DIR = "/var/log/agent/pcaps"
DEFAULT_LOG_DIR = "/var/log/agent/logs"
DEFAULT_TIME_WINDOW = 10
DEFAULT_EXPIRY_DAYS = 30


def call_backend_json(url: str, method: str = "GET", body: dict | None = None,
                       timeout: int = 8) -> dict:
    headers = {"Content-Type": "application/json"}
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
    existing = load_local_config()
    existing.update(data)
    with open(CONFIG_PATH, "w") as f:
        json.dump(existing, f, indent=2)


class SystemInfoWindow(tk.Tk):
    def __init__(self, api_key=None, agent_config=None):
        super().__init__()
        self.api_key = api_key
        self.agent_config = agent_config or {}
        self.paused = False

        self.withdraw()
        self.tk.call("tk", "scaling", WINDOW_SCALE)
        self.title("Cyber Resilience Agent — System Info")
        center_window(self, 650, 390)
        self.resizable(False, False)
        self.deiconify()

        self._build_ui()
        self._refresh_values()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 8}

        header = ttk.Label(self, text="System Information", font=("Segoe UI", 14, "bold"), wraplength=400)
        header.pack(anchor="w", **pad)

        self.organization_var = tk.StringVar(value="")
        self.pcap_dir_var = tk.StringVar(value="")
        self.pcap_time_var = tk.StringVar(value="")
        self.log_dir_var = tk.StringVar(value="")
        self.log_time_var = tk.StringVar(value="")
        self.expiry_var = tk.StringVar(value="")

        self._add_row("Organisation", self.organization_var, None, None)
        self._add_row("PCAP directory", self.pcap_dir_var, "Change", self._change_pcap_dir)
        self._add_row("PCAP time window", self.pcap_time_var, "Change", self._change_pcap_time)
        self._add_row("Log directory", self.log_dir_var, "Change", self._change_log_dir)
        self._add_row("Log time window", self.log_time_var, "Change", self._change_log_time)
        self._add_row("API expiry", self.expiry_var, "Change", self._change_expiry)

        action_frame = ttk.Frame(self)
        action_frame.pack(fill="x", padx=20, pady=(16, 8))

        ttk.Button(action_frame, text="Change password", command=self._open_change_password_window).pack(side="left")
        ttk.Button(action_frame, text="Remove connection", command=self._remove_connection).pack(side="left", padx=(8, 0))
        self.pause_btn = ttk.Button(action_frame, text="Pause connection", command=self._toggle_pause_connection)
        self.pause_btn.pack(side="left", padx=(8, 0))
        ttk.Button(action_frame, text="Delete API key", command=self._delete_api_key).pack(side="left", padx=(8, 0))

    def _add_row(self, title, value_var, button_text, command):
        row = ttk.Frame(self)
        row.pack(fill="x", padx=20, pady=6)

        ttk.Label(row, text=title, width=20, anchor="w").pack(side="left")
        ttk.Label(row, textvariable=value_var, wraplength=240, foreground="#333333").pack(side="left", padx=(8, 0))

        if button_text and command:
            ttk.Button(row, text=button_text, command=command).pack(side="right")

    def _refresh_values(self):
        cfg = load_local_config()
        org_name = self.agent_config.get("org_name") or cfg.get("org_name") or "Unknown org"
        self.organization_var.set(org_name)
        self.pcap_dir_var.set(cfg.get("pcap_watch_dir", DEFAULT_PCAP_DIR))
        self.pcap_time_var.set(f"{cfg.get('pcap_time_window_minutes', DEFAULT_TIME_WINDOW)} mins")
        self.log_dir_var.set(cfg.get("log_watch_dir", DEFAULT_LOG_DIR))
        self.log_time_var.set(f"{cfg.get('log_time_window_minutes', DEFAULT_TIME_WINDOW)} mins")

        expiry_days = cfg.get("api_key_expiry_days", DEFAULT_EXPIRY_DAYS)
        expiry_date = date.today() + timedelta(days=int(expiry_days))
        self.expiry_var.set(expiry_date.strftime("%Y-%m-%d"))

    def _change_pcap_dir(self):
        self._open_directory_editor("pcap_watch_dir", "PCAP Directory", self.pcap_dir_var)

    def _change_log_dir(self):
        self._open_directory_editor("log_watch_dir", "Log Directory", self.log_dir_var)

    def _open_directory_editor(self, config_key, title, value_var):
        win = tk.Toplevel(self)
        win.title(title)
        center_window(win, 420, 220)
        win.transient(self)
        win.grab_set()

        selected_var = tk.StringVar(value=value_var.get())

        ttk.Label(win, text="Choose a directory:").pack(anchor="w", padx=20, pady=(12, 4))
        ttk.Label(win, textvariable=selected_var, wraplength=320).pack(anchor="w", padx=20)

        def pick_dir():
            path = filedialog.askdirectory(title=title)
            if path:
                selected_var.set(path)

        ttk.Button(win, text="Choose Directory", command=pick_dir).pack(pady=(10, 6))
        ttk.Button(win, text="Save", command=lambda: self._save_and_refresh(config_key, selected_var.get(), win)).pack()

    def _change_pcap_time(self):
        self._open_time_editor("pcap_time_window_minutes", "PCAP Time Window", self.pcap_time_var)

    def _change_log_time(self):
        self._open_time_editor("log_time_window_minutes", "Log Time Window", self.log_time_var)

    def _open_time_editor(self, config_key, title, value_var):
        win = tk.Toplevel(self)
        win.title(title)
        center_window(win, 420, 220)
        win.transient(self)
        win.grab_set()

        current_value = int(value_var.get().replace(" mins", "")) if value_var.get() else DEFAULT_TIME_WINDOW
        selected_var = tk.IntVar(value=current_value)

        ttk.Label(win, text="Choose time window (minutes):").pack(anchor="w", padx=20, pady=(12, 4))
        tk.Scale(win, from_=5, to=60, orient="horizontal", variable=selected_var, resolution=1).pack(fill="x", padx=20, pady=(4, 6))
        ttk.Label(win, textvariable=selected_var).pack()

        ttk.Button(win, text="Save", command=lambda: self._save_and_refresh(config_key, selected_var.get(), win)).pack(pady=(8, 0))

    def _change_expiry(self):
        win = tk.Toplevel(self)
        win.withdraw()
        win.title("API Key Expiry")
        center_window(win, 420, 220)
        win.transient(self)
        win.grab_set()
        win.deiconify()

        current_value = int(self._get_config_value("api_key_expiry_days", DEFAULT_EXPIRY_DAYS))
        selected_var = tk.StringVar(value=str(current_value))

        ttk.Label(win, text="Enter number of days (max 30):").pack(anchor="w", padx=20, pady=(12, 6))
        ttk.Entry(win, textvariable=selected_var).pack(fill="x", padx=20)

        def save_expiry():
            try:
                value = int(selected_var.get())
            except ValueError:
                messagebox.showerror("Invalid value", "Please enter a whole number.")
                return

            if value > 30:
                messagebox.showerror("Invalid value", "Maximum expiry is 30 days.")
                return

            self._save_and_refresh("api_key_expiry_days", value, win)

        ttk.Button(win, text="Save", command=save_expiry).pack(pady=(10, 0))

    def _save_and_refresh(self, key, value, window):
        save_local_config({key: value})
        window.destroy()
        self._refresh_values()

    def _open_change_password_window(self):
        win = tk.Toplevel(self)
        win.withdraw()
        win.title("Change Password")
        center_window(win, 460, 260)
        win.transient(self)
        win.grab_set()
        win.deiconify()

        current_var = tk.StringVar()
        new_var = tk.StringVar()
        confirm_var = tk.StringVar()

        ttk.Label(win, text="Current password:").pack(anchor="w", padx=20, pady=(12, 2))
        ttk.Entry(win, textvariable=current_var, show="•").pack(fill="x", padx=20)

        ttk.Label(win, text="New password:").pack(anchor="w", padx=20, pady=(12, 2))
        ttk.Entry(win, textvariable=new_var, show="•").pack(fill="x", padx=20)

        ttk.Label(win, text="Confirm new password:").pack(anchor="w", padx=20, pady=(12, 2))
        ttk.Entry(win, textvariable=confirm_var, show="•").pack(fill="x", padx=20)

        def save_password():
            cfg = load_local_config()
            current_password = cfg.get("password", "")
            if current_var.get() != current_password:
                messagebox.showerror("Invalid password", "Current password is incorrect.")
                return

            if new_var.get() != confirm_var.get():
                messagebox.showerror("Mismatch", "New password and confirm password do not match.")
                return

            save_local_config({"password": new_var.get()})
            messagebox.showinfo("Password changed", "Password updated successfully.")
            win.destroy()

        ttk.Button(win, text="Save", command=save_password).pack(pady=(16, 0))

    def _remove_connection(self):
        confirm = messagebox.askyesno(
            "Remove connection",
            "Removing the connection will forget the current API key and require re-entry. Continue?"
        )
        if not confirm:
            return

        call_backend_json(f"{BASE_URL}/connection/disconnect", method="POST")
        self._go_to_api_key_window()

    def _toggle_pause_connection(self):
        if self.paused:
            call_backend_json(f"{BASE_URL}/connection/resume", method="POST")
            self.paused = False
            self.pause_btn.config(text="Pause connection")
        else:
            call_backend_json(f"{BASE_URL}/connection/pause", method="POST")
            self.paused = True
            self.pause_btn.config(text="Resume connection")

    def _delete_api_key(self):
        confirm = messagebox.askyesno(
            "Delete API key",
            "Deleting the API key will remove the connection and require re-entering the API key. Continue?"
        )
        if not confirm:
            return

        call_backend_json(f"{BASE_URL}-key/delete", method="POST")
        call_backend_json(f"{BASE_URL}/connection/disconnect", method="POST")
        self._go_to_api_key_window()

    def _go_to_api_key_window(self):
        save_local_config({"api_key": None, "org_id": None, "org_name": None, "agent_id": None, "permissions": None})
        self.destroy()
        from TRATA.apikey_window import ApiKeyWindow

        def on_success(api_key, agent_config):
            from TRATA.password_window import PasswordWindow
            pw = PasswordWindow(api_key=api_key, agent_config=agent_config)
            pw.mainloop()

        window = ApiKeyWindow(on_success=on_success)
        window.mainloop()

    def _get_config_value(self, key, default):
        return load_local_config().get(key, default)
