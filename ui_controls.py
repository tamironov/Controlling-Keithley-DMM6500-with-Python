# ui_controls.py
import time
import threading
from queue import Queue
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog

from constants import LUA_AUTORANGE_ON, LUA_AUTORANGE_OFF, LUA_SET_FUNC, LUA_SET_RANGE
from helpers import parse_range, format_reading, parse_float_safe


class ControlPanel:
    """
    Builds the left control panel and contains the measurement worker thread.
    Assumes `self.app` is the main ATEKeithleyApp instance.
    """

    def __init__(self, app):
        self.app = app
        self.parent = app.ctrl_frame

        # ensure runtime attributes on app for compatibility
        self._ensure_app_runtime_attrs()

        self._build_controls()

        # start small UI updater for log queue if not present
        try:
            self.app.after(100, self._ui_update_loop)
        except Exception:
            pass

    def _ensure_app_runtime_attrs(self):
        a = self.app
        if not hasattr(a, "instrument"):
            a.instrument = None
        # instrument dmm/rm and connected state may be provided by InstrumentManager
        if not hasattr(a, "dmm"):
            a.dmm = None
        if not hasattr(a, "rm"):
            a.rm = None
        if not hasattr(a, "connected"):
            a.connected = False
        if not hasattr(a, "running"):
            a.running = False
        if not hasattr(a, "stop_event"):
            import threading
            a.stop_event = threading.Event()
        if not hasattr(a, "pause_event"):
            import threading
            a.pause_event = threading.Event()
        if not hasattr(a, "worker_thread"):
            a.worker_thread = None
        if not hasattr(a, "records"):
            a.records = []
        if not hasattr(a, "plot_data_x"):
            a.plot_data_x = []
        if not hasattr(a, "plot_data_y"):
            a.plot_data_y = []
        if not hasattr(a, "log_queue"):
            a.log_queue = Queue()

    # -------------------------
    # Build UI
    # -------------------------
    def _build_controls(self):
        f = self.parent
        f.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f, text="INSTRUMENT CONTROL", font=("Roboto", 16, "bold")).grid(row=0, column=0, pady=(20, 10))

        # Connection box
        conn_box = ctk.CTkFrame(f)
        conn_box.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        self.device_combo = ctk.CTkComboBox(conn_box, values=[], width=200)
        self.device_combo.pack(pady=5, padx=5, fill="x")
        btn_row = ctk.CTkFrame(conn_box, fg_color="transparent")
        btn_row.pack(fill="x", pady=5)
        ctk.CTkButton(btn_row, text="Scan", width=80, command=self._scan_visa).pack(side="left", padx=5)
        self.connect_btn = ctk.CTkButton(btn_row, text="Connect", width=80, command=self._connect_disconnect, fg_color="green")
        self.connect_btn.pack(side="right", padx=5)

        # Connection box
        conn_box = ctk.CTkFrame(f)
        conn_box.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        self.device_combo = ctk.CTkComboBox(conn_box, values=[], width=200)
        self.device_combo.set("Select Device")     # <---- ADD THIS LINE HERE
        self.device_combo.pack(pady=5, padx=5, fill="x")

        btn_row = ctk.CTkFrame(conn_box, fg_color="transparent")
        btn_row.pack(fill="x", pady=5)

        ctk.CTkButton(btn_row, text="Scan", width=80, command=self._scan_visa).pack(side="left", padx=5)

        self.connect_btn = ctk.CTkButton(
            btn_row,
            text="Connect",
            width=80,
            command=self._connect_disconnect,
            fg_color="green"
        )
        self.connect_btn.pack(side="right", padx=5)


        # Sequence settings
        sett_box = ctk.CTkFrame(f)
        sett_box.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        ctk.CTkLabel(sett_box, text="Sequence Settings", font=("Roboto", 12, "bold")).pack(pady=5)
        self.order_var = ctk.StringVar(value="V->I")
        ctk.CTkOptionMenu(sett_box, values=["V->I", "I->V", "Alternating", "V only", "I only"], variable=self.order_var).pack(fill="x", padx=5, pady=5)
        row_cyc = ctk.CTkFrame(sett_box, fg_color="transparent")
        row_cyc.pack(fill="x", padx=5)
        ctk.CTkLabel(row_cyc, text="Cycles (0=Inf):").pack(side="left")
        self.cycles_entry = ctk.CTkEntry(row_cyc, width=60)
        self.cycles_entry.insert(0, "1")
        self.cycles_entry.pack(side="right")

        # Voltage box
        v_box = ctk.CTkFrame(f, border_width=1, border_color="gray")
        v_box.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(v_box, text="Voltage Phase", text_color="#1f6aa5", font=("Roboto", 13, "bold")).pack(pady=2)
        self._add_param_row(v_box, "Duration (s):", "v_dur", "5")
        self._add_param_row(v_box, "Interval (s):", "v_int", "0.5")
        ctk.CTkLabel(v_box, text="Range:").pack(padx=5)
        self.v_range_var = ctk.StringVar(value="Auto")
        v_options = ["Auto", "100mV", "1V", "3V", "10V"]
        self.v_range_menu = ctk.CTkComboBox(v_box, values=v_options, variable=self.v_range_var)
        self.v_range_menu.pack(fill="x", padx=5, pady=5)
        self.v_autorange = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(v_box, text="Autorange", variable=self.v_autorange).pack(pady=5)

        # Current box
        i_box = ctk.CTkFrame(f, border_width=1, border_color="gray")
        i_box.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(i_box, text="Current Phase", text_color="#d65f5f", font=("Roboto", 13, "bold")).pack(pady=2)
        self._add_param_row(i_box, "Duration (s):", "i_dur", "5")
        self._add_param_row(i_box, "Interval (s):", "i_int", "0.5")
        ctk.CTkLabel(i_box, text="Range:").pack(padx=5)
        self.i_range_var = ctk.StringVar(value="Auto")
        i_options = ["Auto", "10μA", "100μA", "1mA", "10mA", "100mA", "1A", "3A"]
        self.i_range_menu = ctk.CTkComboBox(i_box, values=i_options, variable=self.i_range_var)
        self.i_range_menu.pack(fill="x", padx=5, pady=5)
        self.i_autorange = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(i_box, text="Autorange", variable=self.i_autorange).pack(pady=5)

        # Actions
        act_box = ctk.CTkFrame(f, fg_color="transparent")
        act_box.grid(row=5, column=0, padx=10, pady=20, sticky="ew")
        self.start_btn = ctk.CTkButton(act_box, text="START", height=40, fg_color="#1f6aa5", command=self._start_sequence)
        self.start_btn.pack(fill="x", pady=5)
        grid_act = ctk.CTkFrame(act_box, fg_color="transparent")
        grid_act.pack(fill="x")
        self.pause_btn = ctk.CTkButton(grid_act, text="Pause", width=80, state="disabled", command=self._pause_resume, fg_color="orange")
        self.pause_btn.pack(side="left", padx=2)
        self.stop_btn = ctk.CTkButton(grid_act, text="Stop", width=80, state="disabled", command=self._stop_sequence, fg_color="red")
        self.stop_btn.pack(side="right", padx=2)

        bot_box = ctk.CTkFrame(f, fg_color="transparent")
        bot_box.grid(row=6, column=0, sticky="s", pady=20)
        self.theme_sw = ctk.CTkSwitch(bot_box, text="Dark Mode", command=self._toggle_theme)
        self.theme_sw.pack()

    def _add_param_row(self, parent, label, tag, default):
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", padx=5, pady=1)
        ctk.CTkLabel(fr, text=label).pack(side="left")
        entry = ctk.CTkEntry(fr, width=70)
        entry.insert(0, default)
        entry.pack(side="right")
        setattr(self, f"{tag}_entry", entry)

    # -------------------------
    # UI Update loop (log queue -> app.log)
    # -------------------------
    def _ui_update_loop(self):
        while not self.app.log_queue.empty():
            msg = self.app.log_queue.get()
            # if main app has _log method, use it; else print
            try:
                self.app._log(msg)
            except Exception:
                print(msg)
        # schedule next run
        try:
            self.app.after(200, self._ui_update_loop)
        except Exception:
            pass

    # -------------------------
    # VISA Scan / Connect
    # -------------------------
    def _scan_visa(self):
        try:
            if self.app.instrument:
                resources = self.app.instrument.scan()
            else:
                resources = []
            if resources:
                self.device_combo.configure(values=resources)
                if not self.device_combo.get() and resources:
                    self.device_combo.set(resources[0])
                self._log(f"Found {len(resources)} devices")
            else:
                self.device_combo.configure(values=["No Devices"])
                self.device_combo.set("No Devices")
                self._log("No VISA devices found", "warn")
        except Exception as e:
            self._log(f"VISA Scan Error: {e}", "err")

    def _connect_disconnect(self):
        if getattr(self.app, "connected", False):
            # disconnect
            try:
                if self.app.instrument:
                    self.app.instrument.disconnect()
            except Exception:
                pass
            self.app.connected = False
            self.connect_btn.configure(text="Connect", fg_color="green")
            self._log("Disconnected")
        else:
            addr = self.device_combo.get()
            if not addr or addr == "No Devices":
                messagebox.showwarning("Warning", "No device selected.")
                return
            try:
                if self.app.instrument:
                    idn = self.app.instrument.connect(addr)
                    if idn:
                        self.app.connected = True
                        # instrument manager will have set dmm/rm (if implemented)
                        # fallback to reading from instrument manager result
                        try:
                            # assume instrument manager stored dmm on itself and app.instrument.dmm
                            self.app.dmm = self.app.instrument.dmm
                        except Exception:
                            pass
                        self.connect_btn.configure(text="Disconnect", fg_color="red")
                        self._log(f"Connected: {idn}")
                    else:
                        self.app.connected = False
            except Exception as e:
                self._log(f"Connection failed: {e}", "err")
                messagebox.showerror("Connection Error", str(e))

    def _toggle_theme(self):
        try:
            self.app.set_appearance_mode("dark" if self.theme_sw.get() else "light")
        except Exception:
            pass

    # -------------------------
    # Start / Pause / Stop control
    # -------------------------
    def _start_sequence(self):
        if not getattr(self.app, "connected", False):
            messagebox.showwarning("Warning", "Device not connected")
            return
        if getattr(self.app, "running", False):
            return
        self.app.running = True
        self.app.stop_event.clear()
        self.app.pause_event.clear()
        self.app.worker_thread = threading.Thread(target=self._worker_task, daemon=True)
        self.app.worker_thread.start()
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self._log("Measurement sequence started")

    def _pause_resume(self):
        if self.app.pause_event.is_set():
            self.app.pause_event.clear()
            self.pause_btn.configure(text="Pause")
            self._log("Resumed")
        else:
            self.app.pause_event.set()
            self.pause_btn.configure(text="Resume")
            self._log("Paused")

    def _stop_sequence(self):
        self.app.stop_event.set()
        self.app.running = False
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled", text="Pause")
        self.stop_btn.configure(state="disabled")
        self._log("Measurement stopped")

    # -------------------------
    # Worker thread - performs measurements
    # -------------------------
    def _worker_task(self):
        order = self.order_var.get()
        try:
            cycles = int(self.cycles_entry.get())
        except Exception:
            cycles = 1
        if cycles == 0:
            cycles = float("inf")

        for c in range(cycles):
            for phase in ["VOLTAGE", "CURRENT"]:
                if self.app.stop_event.is_set():
                    return
                if (order == "V only" and phase == "CURRENT") or (order == "I only" and phase == "VOLTAGE"):
                    continue

                dur_entry = getattr(self, f"{phase[0].lower()}_dur_entry")
                int_entry = getattr(self, f"{phase[0].lower()}_int_entry")
                try:
                    duration = float(dur_entry.get())
                except:
                    duration = 5.0
                try:
                    interval = float(int_entry.get())
                except:
                    interval = 0.5

                rng_var = getattr(self, f"{phase[0].lower()}_range_var")
                autorange = getattr(self, f"{phase[0].lower()}_autorange")
                rng_val = parse_range(rng_var.get(), phase)

                # configure instrument via instrument manager or direct dmm
                try:
                    dmm = getattr(self.app, "dmm", None)
                    if autorange.get() or rng_val == "Auto":
                        # autorange on
                        if dmm:
                            dmm.write(LUA_AUTORANGE_ON)
                    else:
                        if dmm:
                            dmm.write(LUA_AUTORANGE_OFF)
                            dmm.write(LUA_SET_FUNC.format(func=phase.lower()))
                            dmm.write(LUA_SET_RANGE.format(rng=rng_val))
                except Exception as e:
                    # log but continue; reading may still be possible
                    self._log(f"Range/config write error: {e}", "warn")

                # measurement loop for this phase
                t0 = time.time()
                while time.time() - t0 < duration:
                    if self.app.stop_event.is_set():
                        return
                    while self.app.pause_event.is_set():
                        time.sleep(0.1)
                    try:
                        dmm = getattr(self.app, "dmm", None)
                        if dmm:
                            val = float(dmm.query("print(dmm.measure.read())"))
                        else:
                            # no instrument: produce NaN
                            val = float("nan")
                    except Exception:
                        val = float("nan")

                    val_txt = format_reading(val, phase)
                    # update center panel live labels if exists
                    try:
                        self.app.center.live_val_lbl.configure(text=val_txt)
                        self.app.center.live_phase_lbl.configure(text=phase)
                    except Exception:
                        pass

                    ts = datetime.now().strftime("%H:%M:%S")
                    self.app.records.append([ts, phase, val_txt])
                    # raw text if center has data_text
                    try:
                        self.app.center.data_text.insert("end", f"{ts}\t{phase}\t{val_txt}\n")
                        self.app.center.data_text.see("end")
                    except Exception:
                        pass

                    self.app.plot_data_x.append(len(self.app.plot_data_x))
                    self.app.plot_data_y.append(val)
                    # update cards
                    try:
                        self.app.center.update_cards(phase)
                    except Exception:
                        pass

                    time.sleep(interval)

        # finished cycles
        self._stop_sequence()

    # -------------------------
    # Card update helper exposed for other modules
    # -------------------------
    def update_cards(self, phase):
        """
        convenience wrapper callable from other modules.
        """
        try:
            self.app.center.update_cards(phase)
        except Exception:
            pass

    # -------------------------
    # Logging helper
    # -------------------------
    def _log(self, msg, level="info"):
        # push string to app.log_queue (consumed by LogPanel)
        try:
            self.app.log_queue.put(f"[{datetime.now().strftime('%H:%M:%S')}] {level.upper()}: {msg}")
        except Exception:
            try:
                self.app._log(msg)
            except Exception:
                print(msg)
