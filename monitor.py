"""
monitor.py — Process-level resource monitoring for pipeline steps.

Usage (in main.py):
    monitor = StepMonitor(interval=2)
    monitor.start("Step 1: Input Reorientation", pid)
    # ... wait for step to finish ...
    rows = monitor.stop()
    save_timeseries(sid, rows, scripts_dir)
    save_step_stats(sid, "Step 1: Input Reorientation", rows, elapsed_minutes, stats_path)
"""

import os
import csv
import time
import threading
import statistics
from datetime import datetime

try:
    import psutil
except ImportError:
    raise ImportError("psutil is required for process-level monitoring. Run: pip install psutil")


def _get_process_tree_stats(pid: int):
    """
    Collect aggregated CPU% and RAM (GB) for a process and all its children.
    Returns (cpu_pct, ram_gb) or (0, 0) if process is gone.
    """
    try:
        root = psutil.Process(pid)
        procs = [root] + root.children(recursive=True)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return 0.0, 0.0

    total_cpu = 0.0
    total_ram = 0.0
    for p in procs:
        try:
            total_cpu += p.cpu_percent(interval=None)
            total_ram += p.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return total_cpu, total_ram / (1024 ** 3)  # bytes → GB


class StepMonitor:
    """
    Monitors a process tree at a fixed interval in a background thread.
    Each sample is (timestamp_str, step_name, cpu_pct, ram_gb).
    """

    def __init__(self, interval: float = 2.0):
        self.interval = interval
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._rows: list[tuple] = []
        self._step_name: str = ""
        self._pid: int = -1

    def start(self, step_name: str, pid: int):
        """Start background sampling for the given PID."""
        self._step_name = step_name
        self._pid = pid
        self._rows = []
        self._stop_event.clear()

        # Prime cpu_percent (first call always returns 0)
        try:
            psutil.Process(pid).cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

        self._thread = threading.Thread(target=self._sample_loop, daemon=True)
        self._thread.start()

    def stop(self) -> list[tuple]:
        """Stop sampling and return collected rows."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self.interval * 2)
        return list(self._rows)

    def _sample_loop(self):
        while not self._stop_event.is_set():
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cpu, ram = _get_process_tree_stats(self._pid)
            self._rows.append((ts, self._step_name, round(cpu, 2), round(ram, 4)))
            self._stop_event.wait(self.interval)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def save_timeseries(sid: str, rows: list[tuple], scripts_dir: str):
    """
    Append rows to resource_timeseries_<sid>.csv inside scripts_dir.
    Columns: Timestamp, Step, CPU_Pct, RAM_GB
    """
    os.makedirs(scripts_dir, exist_ok=True)
    path = os.path.join(scripts_dir, f"resource_timeseries_{sid}.csv")
    write_header = not os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Timestamp", "Step", "CPU_Pct", "RAM_GB"])
        writer.writerows(rows)


def save_step_stats(
    sid: str,
    step_name: str,
    rows: list[tuple],
    elapsed_minutes: float,
    stats_path: str,
):
    """
    Append one summary row to step_stats.csv (shared across all subjects).
    Columns: Subject, Step, RAM_Mean_GB, RAM_Std_GB, Time_Mean_minutes, Time_Std_minutes

    Note: Time_Std_minutes is 0 for a single run; it becomes meaningful when
    multiple subjects accumulate rows for the same step.
    """
    ram_values = [r[3] for r in rows]  # index 3 = RAM_GB
    ram_mean = round(statistics.mean(ram_values), 4) if ram_values else 0.0
    ram_std = round(statistics.stdev(ram_values), 4) if len(ram_values) > 1 else 0.0

    write_header = not os.path.exists(stats_path)
    with open(stats_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow([
                "Subject", "Step",
                "RAM_Mean_GB", "RAM_Std_GB",
                "Time_Mean_minutes", "Time_Std_minutes"
            ])
        writer.writerow([
            sid, step_name,
            ram_mean, ram_std,
            round(elapsed_minutes, 4), 0.0  # Std computed externally if needed
        ])
