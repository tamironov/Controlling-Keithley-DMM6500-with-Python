import pyvisa
from tkinter import messagebox

class InstrumentManager:
    def __init__(self, app):
        self.app = app
        self.rm = None
        self.dmm = None
        self.connected = False

    def scan(self):
        try:
            rm_local = pyvisa.ResourceManager()
            res = list(rm_local.list_resources())
            rm_local.close()
            return res
        except Exception as e:
            self.app._log(f"Scan Error: {e}", "err")
            return []

    def connect(self, resource):
        try:
            self.rm = pyvisa.ResourceManager()
            self.dmm = self.rm.open_resource(resource)
            self.dmm.timeout = 5000

            try:
                idn = self.dmm.query("*IDN?").strip()
            except:
                idn = resource

            self.connected = True
            return idn

        except Exception as e:
            try: self.rm.close()
            except: pass

            self.connected = False
            messagebox.showerror("Connection Error", str(e))
            return None

    def disconnect(self):
        try: 
            if self.dmm: self.dmm.close()
            if self.rm: self.rm.close()
        except: 
            pass
        self.connected = False
