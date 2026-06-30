# NTPrime - Precision Time Configurator ⏱️

**NTPrime** is a modern, lightweight Windows GUI application built with Python and Tkinter. It allows network administrators and power users to easily configure, manage, and monitor their Windows NTP (Network Time Protocol) server settings without having to manually type `w32tm` and `net` commands in the command prompt.

## ⬇️ Download

No Python required — grab the ready-to-run standalone executable:

### ➡️ **[Download NTPrime.exe](https://github.com/saago/NTPrime/raw/main/NTPrime.exe)**

> After downloading, **right-click → Run as administrator** (administrator rights are required to change the time settings).

## ✨ Features

- **Modern UI**: Sleek, flat-design dark mode interface built with native Tkinter.
- **Custom NTP Configuration**: Easily apply one or multiple custom NTP servers (space-separated).
- **Status Check**: Instantly query and display your current NTP configuration and synchronization status.
- **Reset to Defaults**: Quickly restore Windows default time synchronization settings (`time.windows.com`).
- **Live Execution Log**: Monitor the real-time output of background system commands directly in the app.
- **Admin Privilege Check**: Automatically alerts the user if the application isn't run with the necessary Administrator rights.

## 🚀 Prerequisites

- **Operating System**: Windows (the app relies on Windows-specific `w32tm` and `net` commands).
- **Python Environment**: Python 3.6 or newer installed on your system.
- **Privileges**: Administrator privileges are **required** to stop/start the `w32time` service and modify system time configurations.

## 🛠️ Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/saago/NTPrime.git
   cd NTPrime
   ```

2. **Run the application (as Administrator):**
   Open an elevated Command Prompt or PowerShell (Right-click -> Run as Administrator) and execute:
   ```bash
   python ntp_gui.py
   ```

## 📋 How it Works

Under the hood, NTPrime safely automates the execution of the following Windows commands when applying your settings:
```bat
net stop w32time
w32tm /config /syncfromflags:manual /manualpeerlist:"<your_ntp_servers>"
sc config w32time start=auto
net start w32time
w32tm /config /update
w32tm /resync /rediscover
```

## 👨‍💻 Author

Created by **Netanel Elhadad**.

## 📄 License

This project is open-source and available under the [GNU GPL-3.0 License](LICENSE).
