import math

def parse_float_safe(s: str):
    try:
        return float(s.strip())
    except:
        return float("nan")


def format_reading(val, phase):
    if math.isnan(val):
        return "---"

    if phase == "VOLTAGE":
        if abs(val) < 1e-3:
            return f"{val*1e6:.3f} μV"
        elif abs(val) < 1:
            return f"{val*1e3:.3f} mV"
        else:
            return f"{val:.3f} V"

    else:  # CURRENT
        if abs(val) < 1e-6:
            return f"{val*1e9:.3f} nA"
        elif abs(val) < 1e-3:
            return f"{val*1e6:.3f} μA"
        elif abs(val) < 1:
            return f"{val*1e3:.3f} mA"
        else:
            return f"{val:.3f} A"


def parse_range(range_str, phase):
    if range_str.lower() == "auto":
        return "Auto"

    if phase == "VOLTAGE":
        mapping = {"100mV": 0.1, "1V": 1, "3V": 3, "10V": 10}
        return mapping.get(range_str, 10)

    mapping = {
        "10μA": 10e-6, "100μA": 100e-6,
        "1mA": 1e-3, "10mA": 10e-3,
        "100mA": 0.1, "1A": 1, "3A": 3
    }
    return mapping.get(range_str, 1)
