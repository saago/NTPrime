# NTPrime - Precision Time Configurator
# Copyright (c) 2026 Netanel Elhadad
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import ctypes
import sys
import re

# Hide child console windows spawned by subprocess in this windowed app.
CREATE_NO_WINDOW = 0x08000000

# Accepts a hostname or IPv4/IPv6-ish address, optionally followed by a w32time
# flag suffix such as ",0x9". Used to reject anything that could be abused for
# command injection before we hand the value to w32tm.
SERVER_RE = re.compile(r"^[A-Za-z0-9.\-:\[\]]+(,0x[0-9A-Fa-f]+)?$")


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    """Relaunch the program elevated. Returns True if a relaunch was started."""
    try:
        if getattr(sys, "frozen", False):
            # Running as a packaged .exe
            target, params = sys.executable, " ".join(sys.argv[1:])
        else:
            target = sys.executable
            params = " ".join(f'"{a}"' for a in sys.argv)
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", target, params, None, 1)
        return rc > 32  # values <= 32 indicate failure (e.g. user declined UAC)
    except Exception:
        return False


def run_command(cmd):
    """Run a command (list of args) and return (success, output)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="cp862",      # Windows OEM codepage, tolerates Hebrew locales
            errors="replace",
            creationflags=CREATE_NO_WINDOW,
        )
        return result.returncode == 0, (result.stdout or "") + (result.stderr or "")
    except Exception as e:
        return False, str(e)


def normalize_peerlist(raw):
    """Validate user input and build a w32tm manualpeerlist string.

    Returns the peerlist string, or None if any token is invalid.
    Each server gets the ',0x9' flag (client + special-poll-interval) appended
    when no explicit flag was supplied.
    """
    servers = []
    for token in raw.split():
        if not SERVER_RE.match(token):
            return None
        servers.append(token if "," in token else token + ",0x9")
    return " ".join(servers) if servers else None


# ---------------------------------------------------------------------------
# Threaded command execution + thread-safe logging
# ---------------------------------------------------------------------------

def log(msg, tag=None):
    root.after(0, _append_log, msg, tag)


def _append_log(msg, tag):
    log_text.config(state=tk.NORMAL)
    log_text.insert(tk.END, msg, tag)
    log_text.see(tk.END)
    log_text.config(state=tk.DISABLED)


def clear_log():
    log_text.config(state=tk.NORMAL)
    log_text.delete(1.0, tk.END)
    log_text.config(state=tk.DISABLED)


def set_buttons_state(state):
    for b in (apply_btn, status_btn, reset_btn):
        b.config(state=state)


def run_async(worker):
    """Disable buttons, run `worker` in a background thread, re-enable after."""
    set_buttons_state(tk.DISABLED)

    def task():
        try:
            worker()
        finally:
            root.after(0, set_buttons_state, tk.NORMAL)

    threading.Thread(target=task, daemon=True).start()


def execute_commands(commands, success_message):
    clear_log()
    has_error = False
    for cmd in commands:
        log(f"Running: {' '.join(cmd)}\n")
        success, output = run_command(cmd)
        if output:
            log(f"{output}\n")
        if not success:
            log(f"Error running command: {' '.join(cmd)}\n", "error")
            has_error = True

    if has_error:
        root.after(0, lambda: messagebox.showerror(
            "Error",
            "Some commands failed. Please check the log.\n"
            "Did you run the program as Administrator?"))
    else:
        root.after(0, lambda: messagebox.showinfo("Success", success_message))


def build_config_commands(peerlist):
    return [
        ["net", "stop", "w32time"],
        ["w32tm", "/config", "/syncfromflags:manual", f"/manualpeerlist:{peerlist}"],
        ["sc", "config", "w32time", "start=auto"],
        ["net", "start", "w32time"],
        ["w32tm", "/config", "/update"],
        ["w32tm", "/resync", "/rediscover"],
    ]


def apply_ntp():
    raw = ntp_entry.get().strip()
    if not raw:
        messagebox.showwarning("Warning", "Please enter at least one NTP server address.")
        return

    peerlist = normalize_peerlist(raw)
    if peerlist is None:
        messagebox.showerror(
            "Invalid input",
            "One or more server addresses are invalid.\n"
            "Use hostnames or IP addresses separated by spaces.")
        return

    run_async(lambda: execute_commands(
        build_config_commands(peerlist), "NTP configuration applied successfully."))


def reset_default():
    run_async(lambda: execute_commands(
        build_config_commands("time.windows.com,0x9"),
        "Settings reset to default successfully."))


def check_status():
    def worker():
        clear_log()
        for cmd in (["w32tm", "/query", "/configuration"],
                    ["w32tm", "/query", "/status"]):
            log(f"Running: {' '.join(cmd)}\n")
            success, output = run_command(cmd)
            if output:
                log(f"{output}\n")
            if not success:
                log(f"Error:\n{output}\n", "error")

    run_async(worker)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
# --- Modern Dark Mode UI ---
BG_COLOR = "#202124"          # Main Background
CARD_BG = "#292a2d"          # Inner Panel Background
ENTRY_BG = "#3c4043"         # Text Entry Background
FG_COLOR = "#e8eaed"         # Main Text Color
ACCENT_BLUE = "#8ab4f8"      # Modern Blue
ACCENT_GREEN = "#81c995"     # Modern Green
ACCENT_RED = "#f28b82"       # Modern Red
FONT_MAIN = ("Segoe UI", 11)
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_MONO = ("Consolas", 10)

# Try to elevate before building the UI, so the app runs with the rights it needs.
if not is_admin() and relaunch_as_admin():
    sys.exit(0)

root = tk.Tk()
root.title("NTPrime - Precision Time Configurator")
root.geometry("750x600")
root.configure(bg=BG_COLOR)

# Header
header_frame = tk.Frame(root, bg=BG_COLOR)
header_frame.pack(fill=tk.X, pady=(20, 10))

title_lbl = tk.Label(header_frame, text="NTPrime", font=("Segoe UI", 20, "bold"), bg=BG_COLOR, fg=ACCENT_BLUE)
title_lbl.pack()

slogan_lbl = tk.Label(header_frame, text="Precision Time Configurator", font=("Segoe UI", 11, "italic"), bg=BG_COLOR, fg="#9aa0a6")
slogan_lbl.pack()

# Administrator Warning
if not is_admin():
    admin_lbl = tk.Label(root, text="⚠ Warning: The program is not running with Administrator privileges!",
                         fg=ACCENT_RED, bg=BG_COLOR, font=("Segoe UI", 10, "bold"))
    admin_lbl.pack(pady=5)

# Main Panel
card_frame = tk.Frame(root, bg=CARD_BG, padx=25, pady=25)
card_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)

# Input Section
input_frame = tk.Frame(card_frame, bg=CARD_BG)
input_frame.pack(fill=tk.X, pady=(0, 25))

ntp_lbl = tk.Label(input_frame, text="NTP Server Addresses (space-separated):", font=FONT_MAIN, bg=CARD_BG, fg=FG_COLOR)
ntp_lbl.pack(side=tk.LEFT, padx=(0, 10))

ntp_entry = tk.Entry(input_frame, width=35, font=FONT_MAIN, bg=ENTRY_BG, fg=FG_COLOR, insertbackground=FG_COLOR, relief=tk.FLAT)
ntp_entry.pack(side=tk.LEFT, ipady=6, padx=5)

# Buttons Section
btn_frame = tk.Frame(card_frame, bg=CARD_BG)
btn_frame.pack(fill=tk.X, pady=(0, 25))


# Helper function for modern hover buttons
def create_modern_button(parent, text, color, command):
    btn = tk.Button(parent, text=text, command=command, font=("Segoe UI", 10, "bold"),
                    bg=color, fg="#202124", relief=tk.FLAT, activebackground=FG_COLOR, cursor="hand2")
    # Add hover effect (only while the button is enabled)
    btn.bind("<Enter>", lambda e: btn.config(bg=FG_COLOR) if btn["state"] == tk.NORMAL else None)
    btn.bind("<Leave>", lambda e: btn.config(bg=color) if btn["state"] == tk.NORMAL else None)
    btn.pack(side=tk.LEFT, padx=(0, 10), ipadx=15, ipady=6)
    return btn


apply_btn = create_modern_button(btn_frame, "Apply Settings", ACCENT_GREEN, apply_ntp)
status_btn = create_modern_button(btn_frame, "Check Status", ACCENT_BLUE, check_status)
reset_btn = create_modern_button(btn_frame, "Default Settings", ACCENT_RED, reset_default)

# Execution Log
log_lbl = tk.Label(card_frame, text="Execution Log:", font=FONT_MAIN, bg=CARD_BG, fg=FG_COLOR)
log_lbl.pack(anchor=tk.W, pady=(5, 5))

log_text = tk.Text(card_frame, height=13, font=FONT_MONO, bg=ENTRY_BG, fg=FG_COLOR, relief=tk.FLAT, padx=10, pady=10, state=tk.DISABLED)
log_text.pack(fill=tk.BOTH, expand=True)
log_text.tag_config("error", foreground=ACCENT_RED)

# Footer Credit
footer_lbl = tk.Label(root, text="Created by Netanel Elhadad", font=("Segoe UI", 10, "italic"), bg=BG_COLOR, fg="#9aa0a6")
footer_lbl.pack(side=tk.BOTTOM, pady=15)

root.mainloop()
