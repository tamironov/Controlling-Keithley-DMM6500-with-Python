import customtkinter as ctk
from datetime import datetime

class LogPanel:
    def __init__(self, app):
        self.app = app
        self.frame = app.log_frame
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self.frame, text="Event Log", font=("Arial", 12, "bold")
        ).pack(pady=10)

        self.log_box = ctk.CTkTextbox(self.frame, font=("Consolas",10))
        self.log_box.pack(fill="both", expand=True, padx=5, pady=5)

        ctk.CTkButton(
            self.frame, text="Save Log",
            command=self._save_log, height=25
        ).pack(fill="x", padx=5, pady=5)

    def add(self, message, level="info"):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{ts}] {message}\n")
        self.log_box.see("end")

    def _save_log(self):
        file = filedialog.asksaveasfilename(defaultextension=".txt")
        if not file:
            return
        with open(file, "w") as f:
            f.write(self.log_box.get("1.0", "end"))
