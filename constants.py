import customtkinter as ctk

# Appearance
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

# LUA Commands
LUA_SET_FUNC      = "dmm.measure.func = dmm.{func}"
LUA_SET_RANGE     = "dmm.measure.range = {rng}"
LUA_AUTORANGE_ON  = "dmm.measure.autorange = dmm.ON"
LUA_AUTORANGE_OFF = "dmm.measure.autorange = dmm.OFF"
LUA_MEAS_READ     = "print(dmm.measure.read())"
