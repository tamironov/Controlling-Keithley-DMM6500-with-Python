import customtkinter as ctk
from ui_controls import ControlPanel
from ui_center import CenterPanel
from ui_log import LogPanel
from instrument import InstrumentManager

class ATEKeithleyApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("ATE Keithley DMM6500 — Debug Tool")
        self.geometry("1400x900")

        # Main layout
        self.grid_columnconfigure((0,1,2), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.ctrl_frame   = ctk.CTkFrame(self, width=280)
        self.center_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.log_frame    = ctk.CTkFrame(self, width=260)

        self.ctrl_frame.grid(row=0, column=0, sticky="nsew")
        self.center_frame.grid(row=0, column=1, sticky="nsew")
        self.log_frame.grid(row=0, column=2, sticky="nsew")

        # Modules
        self.instrument = InstrumentManager(self)
        self.controls = ControlPanel(self)
        self.center = CenterPanel(self)
        self.log = LogPanel(self)

    def _log(self, msg, level="info"):
        self.log.add(msg, level)
