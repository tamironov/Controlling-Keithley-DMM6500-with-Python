# ATE Keithley DMM6500 Debugging Tool

A Python-based **Automatic Test Equipment (ATE) tool** for the **Keithley DMM6500** digital multimeter.  
Designed for electronics engineers and technicians, it provides an interactive GUI for performing voltage and current measurement sequences, live plotting, and automated data logging.

---

## Features

- **Multi-phase Measurement Sequences**: Voltage-first, current-first, alternating, or single-phase sequences with configurable cycles, durations, and intervals.
- **Selectable Ranges & Autoranging**: Choose specific voltage/current ranges or enable autoranging.
- **Real-time Data Visualization**: Live plots with auto-scaling and clear axis labels.
- **Dashboard & Stats**: Displays live readings, phase indicators, and summary cards showing min, max, and average values.
- **Data Logging & Export**: Records measurements with timestamps and exports to CSV for post-analysis.
- **Responsive & Threaded**: Multi-threaded design ensures smooth GUI operation during measurement sequences.
- **CustomTkinter Interface**: Modern, theme-switchable GUI with controls, dashboard, and log panels.
- **Event Logging**: Timestamped logs for traceability and debugging.

---

## Requirements

- Python 3.10+  
- [PyVISA](https://pypi.org/project/PyVISA/)  
- [CustomTkinter](https://pypi.org/project/customtkinter/)  
- [Matplotlib](https://pypi.org/project/matplotlib/)  
- A working VISA backend (NI-VISA or pyvisa-py)

---

## Installation

Clone the repository and install dependencies:

```bash
