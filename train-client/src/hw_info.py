import psutil
import time

class HWInfo:
    def __init__(self):
        self._prev_disk_read = None
        self._prev_disk_write = None
        self._prev_time = None

    def get_hw_info(self):
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
        now = time.time()
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

        return {
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
