#!/usr/bin/env python3
"""Check this machine against the official FLOP Miner / Validator specs.

Read-only. It looks at CPU cores, RAM, free disk and, if nvidia-smi is
present, GPU memory. It sends nothing anywhere and installs nothing.

Official requirements (flop.finance/testnet, 25 November 2026):
  Miner:     GPU with 16 GB or more VRAM per unit
  Validator: 8+ CPU cores, 64 GB RAM, 4 TB NVMe (2 TB minimum), 1 Gbps link
"""
import os
import platform
import shutil
import subprocess
import sys


def ram_gb():
    try:
        if sys.platform.startswith("win"):
            import ctypes

            class MemoryStatus(ctypes.Structure):
                _fields_ = [
                    ("length", ctypes.c_ulong),
                    ("memory_load", ctypes.c_ulong),
                    ("total_phys", ctypes.c_ulonglong),
                    ("avail_phys", ctypes.c_ulonglong),
                    ("total_page_file", ctypes.c_ulonglong),
                    ("avail_page_file", ctypes.c_ulonglong),
                    ("total_virtual", ctypes.c_ulonglong),
                    ("avail_virtual", ctypes.c_ulonglong),
                    ("avail_extended_virtual", ctypes.c_ulonglong),
                ]

            status = MemoryStatus()
            status.length = ctypes.sizeof(MemoryStatus)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status))
            return status.total_phys / (1024 ** 3)
        if sys.platform.startswith("linux"):
            with open("/proc/meminfo", encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("MemTotal:"):
                        return int(line.split()[1]) / (1024 ** 2)
        if sys.platform == "darwin":
            out = subprocess.run(
                ["sysctl", "-n", "hw.memsize"],
                capture_output=True, text=True, timeout=10,
            )
            return int(out.stdout.strip()) / (1024 ** 3)
    except Exception:
        return None
    return None


def gpu_vram_gb():
    """Return the largest NVIDIA GPU memory in GB, or None if unknown."""
    exe = shutil.which("nvidia-smi")
    if not exe:
        return None
    try:
        out = subprocess.run(
            [exe, "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15,
        )
        values = [float(line.strip()) for line in out.stdout.splitlines() if line.strip()]
        if values:
            return max(values) / 1024
    except Exception:
        return None
    return None


def main():
    cores = os.cpu_count() or 0
    ram = ram_gb()
    disk_free_tb = shutil.disk_usage(os.path.expanduser("~")).free / (1024 ** 4)
    gpu = gpu_vram_gb()

    print(f"System : {platform.system()} {platform.release()} ({platform.machine()})")
    print(f"CPU    : {platform.processor() or 'name not reported'} - {cores} logical cores")
    print(f"RAM    : {ram:.1f} GB" if ram else "RAM    : could not be read, check it by hand")
    print(f"Disk   : {disk_free_tb:.2f} TB free on the home drive")
    print(f"GPU    : {gpu:.1f} GB VRAM (NVIDIA)" if gpu else
          "GPU    : no NVIDIA GPU found by nvidia-smi. On Windows, check Task Manager, Performance, GPU for the VRAM figure.")

    print()
    if gpu is None:
        print("Miner     : cannot decide here, I need the VRAM figure. 16 GB or more passes.")
    elif gpu >= 16:
        print("Miner     : VRAM passes the 16 GB requirement. The miner client and onboarding still have to be open.")
    else:
        print(f"Miner     : NO. {gpu:.1f} GB VRAM is below the 16 GB requirement.")

    problems = []
    if cores < 8:
        problems.append(f"CPU cores {cores} < 8")
    if ram is not None and ram < 64:
        problems.append(f"RAM {ram:.0f} GB < 64 GB")
    if disk_free_tb < 2:
        problems.append(f"free disk {disk_free_tb:.2f} TB < 2 TB minimum")
    if problems:
        print("Validator : NO. " + "; ".join(problems) + ". Internet speed was not tested, 1 Gbps is also required.")
    else:
        print("Validator : hardware looks close on the figures read here. Internet speed (1 Gbps) and the full 4 TB NVMe recommendation still need checking.")

    print()
    print("Agent is the remaining role: it needs a DID and a wallet, not a big GPU or 64 GB of RAM.")
    print("See docs/ROADMAP.md for what has to open officially before that step counts.")


if __name__ == "__main__":
    main()
