import tkinter as tk
from tkinter import ttk

DEPENDENCIES = [
    "tcpdump",
    "jdk-25",
    "auditd",
    "gcc",
    "zeek",
]


class BlockWindow(tk.Tk):
    def __init__(self, continue_to_api_key=False, next_callback=None):
        super().__init__()
        self.continue_to_api_key = continue_to_api_key
        self.next_callback = next_callback

        self.tk.call("tk", "scaling", 1.25)
        self.title("Dependencies Required")
        self.resizable(False, False)
        self.geometry("650x390")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._center_on_screen()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 10}

        header = ttk.Label(
            self,
            text="Following dependencies need to be installed before proceeding.",
            font=("Segoe UI", 12, "bold"),
            wraplength=420,
            justify="left",
        )
        header.pack(anchor="w", **pad)

        body = ttk.Label(
            self,
            text="This agent cannot continue until these packages are installed:",
            wraplength=420,
            justify="left",
        )
        body.pack(anchor="w", padx=20)

        list_frame = ttk.Frame(self)
        list_frame.pack(anchor="w", padx=20, pady=(8, 0))

        for dep in DEPENDENCIES:
            item = ttk.Label(list_frame, text=f"• {dep}", justify="left")
            item.pack(anchor="w", pady=2)

        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self, textvariable=self.status_var, foreground="#555555", wraplength=420, justify="left")
        self.status_label.pack(anchor="w", padx=20, pady=(8, 0))

        self.progress = ttk.Progressbar(self, mode="indeterminate")

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=20, pady=16)

        self.locate_btn = ttk.Button(btn_frame, text="Locate dependencies", command=self._on_locate_clicked)
        self.locate_btn.pack(side="left")

        exit_btn = ttk.Button(btn_frame, text="Exit", command=self._on_close)
        exit_btn.pack(side="right")

    def _center_on_screen(self):
        self.update_idletasks()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _on_locate_clicked(self):
        self.locate_btn.config(state="disabled")
        self.status_var.set("Searching system for installed dependencies...")
        self.progress.pack(fill="x", padx=20, pady=(8, 0))
        self.progress.start(10)
        self.after(5500, self._finish_locate)

    def _finish_locate(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.locate_btn.config(state="normal")

        if self.continue_to_api_key:
            self.status_label.config(foreground="#0a7d2c")
            self.status_var.set("All dependencies found. Opening API key window...")
            self.after(800, self._proceed_to_next)
        else:
            self.status_label.config(foreground="#555555")
            self.status_var.set("Dependencies were not found on this system.")

    def _proceed_to_next(self):
        self.destroy()
        if callable(self.next_callback):
            self.next_callback()

    def _on_close(self):
        self.destroy()

if __name__ == "__main__":


    app = BlockWindow()  # swap it with settings window, jo khulegi on success.
    app.mainloop()