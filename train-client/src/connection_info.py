"""Utilities for identifying the network interface used for an NTP request."""
from __future__ import annotations

import os
import re
import socket
import subprocess
import sys
from typing import Optional

import psutil


def _interface_for_host(host: str) -> Optional[str]:
    """Return the name of the local interface routed to ``host``, if any."""
    try:
        addresses = socket.getaddrinfo(host, 123, type=socket.SOCK_DGRAM)
    except OSError:
        return None

    local_address: Optional[str] = None
    for family, socket_type, protocol, _, address in addresses:
        try:
            with socket.socket(family, socket_type, protocol) as route_socket:
                route_socket.connect(address)
                local_address = route_socket.getsockname()[0]
                break
        except OSError:
            continue

    if not local_address:
        return None

    for interface_name, address_entries in psutil.net_if_addrs().items():
        if any(entry.address == local_address for entry in address_entries):
            return interface_name
    return None


def _is_wifi_interface(interface_name: str) -> bool:
    if sys.platform == "win32":
        output = _run_command(["netsh", "wlan", "show", "interfaces"])
        return bool(
            re.search(
                rf"^\s*Name\s*:\s*{re.escape(interface_name)}\s*$",
                output,
                re.MULTILINE,
            )
        )

    if sys.platform == "darwin":
        output = _run_command(["networksetup", "-listallhardwareports"])
        sections = re.split(r"(?=^Hardware Port:)", output, flags=re.MULTILINE)
        return any(
            "Hardware Port: Wi-Fi" in section and f"Device: {interface_name}" in section
            for section in sections
        )

    # Linux: a "wireless" subdirectory is only present for Wi-Fi interfaces.
    return os.path.isdir(f"/sys/class/net/{interface_name}/wireless")


def _run_command(arguments: list[str]) -> str:
    try:
        result = subprocess.run(
            arguments,
            capture_output=True,
            check=False,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.strip()


def _wifi_ssid(interface_name: str) -> Optional[str]:
    if sys.platform == "win32":
        output = _run_command(["netsh", "wlan", "show", "interfaces"])
        sections = re.split(r"(?=^\s*Name\s*:)", output, flags=re.MULTILINE)
        for section in sections:
            name = re.search(r"^\s*Name\s*:\s*(.+?)\s*$", section, re.MULTILINE)
            state = re.search(
                r"^\s*State\s*:\s*connected\s*$",
                section,
                re.MULTILINE | re.IGNORECASE,
            )
            ssid = re.search(r"^\s*SSID\s*:\s*(.+?)\s*$", section, re.MULTILINE)
            if name and name.group(1) == interface_name and state and ssid:
                return ssid.group(1)
        return None

    if sys.platform == "darwin":
        output = _run_command(
            ["networksetup", "-getairportnetwork", interface_name]
        )
        prefix = "Current Wi-Fi Network:"
        for line in output.splitlines():
            if line.startswith(prefix):
                return line[len(prefix):].strip() or None
        return None

    output = _run_command(["iwgetid", interface_name, "--raw"])
    if output:
        return output

    output = _run_command(
        [
            "nmcli",
            "--terse",
            "--fields",
            "IN-USE,SSID",
            "device",
            "wifi",
            "list",
            "ifname",
            interface_name,
        ]
    )
    for line in output.splitlines():
        if line.startswith("*:"):
            return line[2:].replace("\\:", ":").replace("\\\\", "\\").strip() or None
    return None


def get_network_connection(host: str) -> str:
    """Return the routed interface type and Wi-Fi SSID for an NTP host."""
    interface_name = _interface_for_host(host)
    if interface_name is None:
        return "Unknown"

    if _is_wifi_interface(interface_name):
        ssid = _wifi_ssid(interface_name)
        return f"Wi-Fi ({ssid})" if ssid else "Wi-Fi (SSID unavailable)"

    return "Ethernet"
