import os
import threading

from app_logger import logger


def pin_current_thread(cpus):
    """Pin the calling thread to the given CPU set.

    os.sched_setaffinity is Linux-only; on other platforms (Windows, macOS)
    or when the CPUs don't exist, this is a no-op.
    """
    if not hasattr(os, "sched_setaffinity"):
        return
    try:
        os.sched_setaffinity(threading.get_native_id(), cpus)
    except (OSError, ValueError) as e:
        logger.warning(f"Could not set CPU affinity to {cpus}: {e}")
