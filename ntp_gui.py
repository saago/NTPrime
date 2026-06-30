import tkinter as tk
from tkinter import messagebox
import subprocess
import ctypes
import sys

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_command(cmd):
    try:
        # Run command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def apply_ntp():
    ntp_servers = ntp_entry.get().strip()
    if not ntp_servers:
        messagebox.showwarning("Warning", "Please enter at least one NTP server address.")
        return

    commands = [
        "net stop w32time",
        f'w32tm /config /syncfromflags:manual /manualpeerlist:"{ntp_servers}"',
        "sc config w32time start=auto",
        "net start w32time",
        "w32tm /config /update",
        "w32tm /resync /rediscover"
    ]

    execute_commands(commands, "NTP configuration applied successfully.")

def check_status():
    log_text.config(state=tk.NORMAL)
    log_text.delete(1.0, tk.END)
    
    cmds = [
        "w32tm /query /configuration",
        "w32tm /query /status"
    ]
    
    for cmd in cmds:
        log_text.insert(tk.END, f"Running: {cmd}\n")
        success, output = run_command(cmd)
        if output:
            log_text.insert(tk.END, f"{output}\n")
        if not success:
             log_text.insert(tk.END, f"Error:\n{output}\n", "error")
             
    log_text.config(state=tk.DISABLED)

def reset_default():
    # Windows default settings
    commands = [
        "net stop w32time",
        'w32tm /config /syncfromflags:manual /manualpeerlist:"time.windows.com,0x9"',
        "sc config w32time start=auto",
        "net start w32time",
        "w32tm /config /update",
        "w32tm /resync /rediscover"
    ]
    
    execute_commands(commands, "Settings reset to default successfully.")

def execute_commands(commands, success_message):
    log_text.config(state=tk.NORMAL)
    log_text.delete(1.0, tk.END)
    has_error = False
    
    for cmd in commands:
        log_text.insert(tk.END, f"Running: {cmd}\n")
        root.update()
        success, output = run_command(cmd)
        
        if output:
            log_text.insert(tk.END, f"{output}\n")
            
        if not success:
            log_text.insert(tk.END, f"Error running command: {cmd}\n", "error")
            has_error = True
            
        root.update()
        
    log_text.config(state=tk.DISABLED)

    if has_error:
        messagebox.showerror("Error", "Some commands failed. Please check the log.\nDid you run the program as Administrator?")
    else:
        messagebox.showinfo("Success", success_message)


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
    # Add hover effect
    btn.bind("<Enter>", lambda e: btn.config(bg=FG_COLOR))
    btn.bind("<Leave>", lambda e: btn.config(bg=color))
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
