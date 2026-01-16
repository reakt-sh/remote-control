import psutil
import datetime
import os
from globals import HW_USAGE_DUMP
class HWInfo:
    def __init__(self):
        self._prev_disk_read = None
        self._prev_disk_write = None
        self._prev_time = None
        self.hw_usage_output_file = None
        self.create_dump_file_for_hw_usage()

    def create_dump_file_for_hw_usage(self):
        dump_dir = os.path.dirname(HW_USAGE_DUMP)
        if dump_dir and not os.path.exists(dump_dir):
            os.makedirs(dump_dir, exist_ok=True)
        output_filename = f"{HW_USAGE_DUMP}.log"

        # create a new file only if it doesn't exist
        if not os.path.exists(output_filename):
            self.hw_usage_output_file = open(output_filename, 'w')
        else:
            self.hw_usage_output_file = open(output_filename, 'a')

    def notify_new_remote_control_connected(self, remote_control_id: str):
        if self.hw_usage_output_file:
            self.hw_usage_output_file.write(f"New remote control connected: {remote_control_id}\n")
            self.hw_usage_output_file.flush()


    def get_hw_info(self, write_to_file = False):
        cpu = psutil.cpu_percent(interval=None)
        freq_info = psutil.cpu_freq()
        freq = int(freq_info.current) if freq_info else 0
        temps = psutil.sensors_temperatures() if hasattr(psutil, "sensors_temperatures") else {}
        temp_val = None
        if temps:
            for entries in temps.values():
                if entries:
                    cur = entries[0].current if hasattr(entries[0], "current") else None
                    if cur is not None:
                        temp_val = cur
                        break
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage('/')
        io = psutil.disk_io_counters() if hasattr(psutil, "disk_io_counters") else None
        now = int(datetime.datetime.now().timestamp() * 1000)
        read_mb_s = 0.0
        write_mb_s = 0.0
        if io:
            if self._prev_disk_read is not None and self._prev_disk_write is not None and self._prev_time is not None:
                dt = max(now - self._prev_time, 1e-6)
                read_mb_s = (io.read_bytes - self._prev_disk_read) / dt / (1024 * 1024)
                write_mb_s = (io.write_bytes - self._prev_disk_write) / dt / (1024 * 1024)
            self._prev_disk_read = io.read_bytes
            self._prev_disk_write = io.write_bytes
            self._prev_time = now
        used_mb = int(mem.used / (1024 * 1024))
        total_gb = mem.total / (1024 * 1024 * 1024)
        swap_mb = int(swap.used / (1024 * 1024))
        ghz = freq / 1000.0 if freq else 0.0

        hw_usage_log_entry = {
            "created_at": now,
            "cpu_usage_percent": int(cpu),
            "cpu_frequency_ghz": ghz,
            "cpu_temperature_celsius": temp_val,
            "ram_used_mb": used_mb,
            "ram_total_gb": total_gb,
            "ram_usage_percent": int(mem.percent),
            "swap_used_mb": swap_mb,
            "disk_usage_percent": int(disk.percent),
            "disk_read_mb_s": read_mb_s,
            "disk_write_mb_s": write_mb_s,
        }

        if write_to_file and self.hw_usage_output_file:
            self.hw_usage_output_file.write(f"{hw_usage_log_entry}\n")
            self.hw_usage_output_file.flush()

        return hw_usage_log_entry
