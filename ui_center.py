# ui_center.py
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import customtkinter as ctk
from tkinter import filedialog
from helpers import parse_float_safe

class CenterPanel:
    """
    Builds the center dashboard: tabs, plot, cards, raw data.
    Expects `self.app` to be the main ATEKeithleyApp.
    """

    def __init__(self, app):
        self.app = app
        self.parent = app.center_frame

        # ensure minimal attributes
        if not hasattr(self.app, "plot_data_x"):
            self.app.plot_data_x = []
        if not hasattr(self.app, "plot_data_y"):
            self.app.plot_data_y = []
        if not hasattr(self.app, "records"):
            self.app.records = []

        self._build_center_panel()
        # small redraw loop for canvas
        try:
            self.app.after(200, self._plot_update_loop)
        except Exception:
            pass

    def _build_center_panel(self):
        self.tabs = ctk.CTkTabview(self.parent)
        self.tabs.pack(fill="both", expand=True)
        self.tabs.add("Dashboard")
        self.tabs.add("Raw Data")

        dash = self.tabs.tab("Dashboard")
        dash.grid_columnconfigure(0, weight=1)
        dash.grid_rowconfigure(1, weight=1)

        # Status row
        stat_fr = ctk.CTkFrame(dash, height=50)
        stat_fr.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        self.status_lbl = ctk.CTkLabel(stat_fr, text="Status: IDLE", font=("Arial", 16, "bold"))
        self.status_lbl.pack(side="left", padx=20)
        self.live_val_lbl = ctk.CTkLabel(stat_fr, text="---", font=("Consolas", 24, "bold"), text_color="#1f6aa5")
        self.live_val_lbl.pack(side="right", padx=20)
        self.live_phase_lbl = ctk.CTkLabel(stat_fr, text="", font=("Arial", 12))
        self.live_phase_lbl.pack(side="right", padx=5)

        # Plot area
        self.plot_frame = ctk.CTkFrame(dash)
        self.plot_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.fig, self.ax = plt.subplots(figsize=(6, 4), dpi=100)
        self.ax.set_title("Real-time Measurement")
        self.ax.set_xlabel("Samples")
        self.ax.set_ylabel("Amplitude")
        self.ax.grid(True, linestyle='--', alpha=0.6)
        self.line, = self.ax.plot([], [], linewidth=1.5)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Cards frame
        card_fr = ctk.CTkFrame(dash, height=120)
        card_fr.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        card_fr.grid_columnconfigure((0, 1), weight=1)
        self.card_v = self._create_stat_card(card_fr, "Voltage Summary", 0, "#e3f2fd", "black")
        self.card_i = self._create_stat_card(card_fr, "Current Summary", 1, "#fbe9e7", "black")

        # Raw Data tab
        self.data_text = ctk.CTkTextbox(self.tabs.tab("Raw Data"), font=("Consolas", 11))
        self.data_text.pack(fill="both", expand=True, padx=5, pady=5)
        btn_fr = ctk.CTkFrame(self.tabs.tab("Raw Data"))
        btn_fr.pack(fill="x", pady=5)
        ctk.CTkButton(btn_fr, text="Export CSV", command=self._export_csv).pack(side="right", padx=10)
        ctk.CTkButton(btn_fr, text="Clear Data", command=self._clear_data).pack(side="right", padx=10)

    def _create_stat_card(self, parent, title, col, bg_color, txt_color):
        f = ctk.CTkFrame(parent, fg_color=bg_color)
        f.grid(row=0, column=col, sticky="nsew", padx=5, pady=5)
        ctk.CTkLabel(f, text=title, text_color=txt_color, font=("Arial", 12, "bold")).pack(pady=5)
        lbls = {}
        for k in ["Min", "Max", "Avg"]:
            r = ctk.CTkFrame(f, fg_color="transparent", height=20)
            r.pack(fill="x", padx=10)
            ctk.CTkLabel(r, text=k, text_color=txt_color).pack(side="left")
            l = ctk.CTkLabel(r, text="---", text_color=txt_color, font=("Consolas", 12, "bold"))
            l.pack(side="right")
            lbls[k.lower()] = l
        # store on self for easy update
        setattr(self, f"lbls_{title.split()[0].lower()}", lbls)
        return f

    # -------------------------
    # Plot update loop
    # -------------------------
    def _plot_update_loop(self):
        try:
            if len(self.app.plot_data_x) > 0:
                self.line.set_data(self.app.plot_data_x, self.app.plot_data_y)
                self.ax.relim()
                self.ax.autoscale_view()
                try:
                    self.canvas.draw_idle()
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.app.after(200, self._plot_update_loop)
        except Exception:
            pass

    # -------------------------
    # CSV / Raw data helpers
    # -------------------------
    def _export_csv(self):
        if not getattr(self.app, "records", []):
            try:
                ctk.CTkMessageBox(title="Export", message="No data to export.")
            except Exception:
                pass
            return
        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")])
        if file:
            try:
                with open(file, "w", newline="") as f:
                    import csv
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Phase", "Value"])
                    for r in self.app.records:
                        writer.writerow(r)
                # log via app
                try:
                    self.app._log(f"Data exported: {file}")
                except Exception:
                    pass
            except Exception as e:
                try:
                    self.app._log(f"CSV export error: {e}", "err")
                except Exception:
                    pass

    def _clear_data(self):
        self.app.records.clear()
        try:
            self.data_text.delete("1.0", "end")
        except Exception:
            pass
        self.app.plot_data_x.clear()
        self.app.plot_data_y.clear()
        # update cards to blank
        for attr in ("lbls_voltage", "lbls_current"):
            if hasattr(self, attr):
                lbls = getattr(self, attr)
                for k in lbls:
                    lbls[k].configure(text="---")

    # -------------------------
    # Card updater (call from worker)
    # -------------------------
    def update_cards(self, phase):
        # gather numeric values from records for this phase
        vals = []
        for r in self.app.records:
            if r[1] == phase:
                # r[2] is formatted like "1.23 V" or "---"
                first_tok = str(r[2]).split()[0]
                v = parse_float_safe(first_tok)
                if not (v != v):  # not NaN
                    vals.append(v)
        if not vals:
            return
        if phase == "VOLTAGE":
            lbls = getattr(self, "lbls_voltage", None)
        else:
            lbls = getattr(self, "lbls_current", None)

        if not lbls:
            return

        try:
            lbls["min"].configure(text=f"{min(vals):.3g}")
            lbls["max"].configure(text=f"{max(vals):.3g}")
            lbls["avg"].configure(text=f"{sum(vals)/len(vals):.3g}")
        except Exception:
            pass
