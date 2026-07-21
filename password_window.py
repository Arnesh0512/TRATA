import json
import os
import tkinter as tk
from tkinter import messagebox, ttk

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


class PasswordWindow(tk.Tk):
    def __init__(self, api_key: str, agent_config: dict):
        super().__init__()
        self.api_key = api_key
        self.agent_config = agent_config or {}
        self.password_key = "password"

        self.withdraw()
        self.tk.call("tk", "scaling", WINDOW_SCALE)
        self.title("Cyber Resilience Agent — Verify Identity")
        center_window(self, 560, 330)
        self.resizable(False, False)
        self.deiconify()

        self.password_var = tk.StringVar()
        self.confirm_var = tk.StringVar()
        self.new_password_var = tk.StringVar()

        if self._password_exists():
            self._build_verify_ui()
        else:
            self._build_set_password_ui()

    def _password_exists(self) -> bool:
        return bool(load_local_config().get(self.password_key))

    def _build_verify_ui(self):
        pad = {"padx": 20, "pady": 8}
        ttk.Label(self, text="Enter your password", font=("Segoe UI", 14, "bold")).pack(anchor="w", **pad)

        ttk.Label(self, text="Password:").pack(anchor="w", padx=20, pady=(8, 2))
        ttk.Entry(self, textvariable=self.password_var, show="•", width=40).pack(anchor="w", padx=20)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=20, pady=16)
        ttk.Button(btn_frame, text="Verify", command=self._verify_password).pack(side="right")

        reset_btn = ttk.Button(self, text="Reset password", command=self._reset_password)
        reset_btn.pack(anchor="w", padx=20)

        self.bind("<Return>", lambda event: self._verify_password())

    def _build_set_password_ui(self):
        pad = {"padx": 20, "pady": 8}
        ttk.Label(self, text="Set a password", font=("Segoe UI", 14, "bold")).pack(anchor="w", **pad)

        ttk.Label(self, text="Password:").pack(anchor="w", padx=20, pady=(8, 2))
        ttk.Entry(self, textvariable=self.password_var, show="•", width=40).pack(anchor="w", padx=20)

        ttk.Label(self, text="Confirm password:").pack(anchor="w", padx=20, pady=(8, 2))
        ttk.Entry(self, textvariable=self.confirm_var, show="•", width=40).pack(anchor="w", padx=20)

        ttk.Button(self, text="Save password", command=self._save_password).pack(anchor="e", padx=20, pady=16)
        self.bind("<Return>", lambda event: self._save_password())

    def _verify_password(self):
        existing_password = load_local_config().get(self.password_key, "")
        if self.password_var.get() == existing_password:
            self.destroy()
            from system_info_window import SystemInfoWindow
            window = SystemInfoWindow(api_key=self.api_key, agent_config=self.agent_config)
            window.mainloop()
        else:
            messagebox.showerror("Invalid password", "The password you entered is incorrect.")

    def _save_password(self):
        password = self.password_var.get()
        confirm = self.confirm_var.get()

        if not password or not confirm:
            messagebox.showerror("Missing value", "Please fill both password fields.")
            return

        if password != confirm:
            messagebox.showerror("Mismatch", "Password and confirm password do not match.")
            return

        save_local_config({self.password_key: password})
        messagebox.showinfo("Saved", "Password saved successfully.")
        self.destroy()
        from system_info_window import SystemInfoWindow
        window = SystemInfoWindow(api_key=self.api_key, agent_config=self.agent_config)
        window.mainloop()

    def _reset_password(self):
        confirm = messagebox.askyesno(
            "Reset password",
            "Proceeding will remove the current connection and require entering the API key again. Continue?"
        )
        if not confirm:
            return

        save_local_config({"api_key": None, "org_id": None, "org_name": None, "agent_id": None, "permissions": None, self.password_key: None})
        self.destroy()
        from apikey_window import ApiKeyWindow

        def on_success(api_key, agent_config):
            pw = PasswordWindow(api_key=api_key, agent_config=agent_config)
            pw.mainloop()

        window = ApiKeyWindow(on_success=on_success)
        window.mainloop()
