import platform
import sys
import traceback
from pathlib import Path
import subprocess
import os

import requests
from packaging.version import parse as parse_version
from pymobiledevice3.cli.cli_common import Command
from pymobiledevice3.exceptions import NoDeviceConnectedError, PyMobileDevice3Exception
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3.services.installation_proxy import InstallationProxyService
from sparserestore import backup, perform_restore
import tkinter as tk
from tkinter import messagebox, filedialog


def exit_app(code=0):
    if platform.system() == "Windows" and getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        input("Press Enter to exit...")

    sys.exit(code)


def replace_app(service_provider, app_name):
    os_names = {
        "iPhone": "iOS",
        "iPad": "iPadOS",
        "iPod": "iOS",
        "AppleTV": "tvOS",
        "Watch": "watchOS",
        "AudioAccessory": "HomePod Software Version",
        "RealityDevice": "visionOS",
    }

    device_class = service_provider.get_value(key="DeviceClass")
    device_build = service_provider.get_value(key="BuildVersion")
    device_version = parse_version(service_provider.product_version)

    if not all([device_class, device_build, device_version]):
        messagebox.showerror("Error", "Failed to get device information! Make sure your device is connected and try again.")
        return

    os_name = (os_names[device_class] + " ") if device_class in os_names else ""
    if (
        device_version < parse_version("15.0")
        or device_version > parse_version("17.0")
        or parse_version("16.7") < device_version < parse_version("17.0")
        or device_version == parse_version("16.7")
        and device_build != "20H18"  # 16.7 RC
    ):
        messagebox.showerror(
            "Error", f"{os_name}{device_version} ({device_build}) is not supported.\nThis tool is only compatible with iOS/iPadOS 15.0 - 16.7 RC and 17.0."
        )
        return

    if not app_name.endswith(".app"):
        app_name += ".app"

    apps_json = InstallationProxyService(service_provider).get_apps(application_type="System", calculate_sizes=False)

    app_path = None
    for key, value in apps_json.items():
        if isinstance(value, dict) and "Path" in value:
            potential_path = Path(value["Path"])
            if potential_path.name.lower() == app_name.lower():
                app_path = potential_path
                app_name = app_path.name

    if not app_path:
        messagebox.showerror("Error", f"Failed to find the removable system app '{app_name}'! Make sure the app is installed.")
        return
    elif Path("/private/var/containers/Bundle/Application") not in app_path.parents:
        messagebox.showerror("Error", f"'{app_name}' is not a removable system app! Please choose a removable system app.")
        return

    app_uuid = app_path.parent.name

    try:
        response = requests.get("https://github.com/opa334/TrollStore/releases/latest/download/PersistenceHelper_Embedded")
        response.raise_for_status()
        helper_contents = response.content
    except Exception as e:
        messagebox.showerror("Error", f"Failed to download TrollStore Helper: {e}")
        return

    back = backup.Backup(
        files=[
            backup.Directory("", "RootDomain"),
            backup.Directory("Library", "RootDomain"),
            backup.Directory("Library/Preferences", "RootDomain"),
            backup.ConcreteFile("Library/Preferences/temp", "RootDomain", owner=33, group=33, contents=helper_contents, inode=0),
            backup.Directory(
                "",
                f"SysContainerDomain-../../../../../../../../var/backup/var/containers/Bundle/Application/{app_uuid}/{app_name}",
                owner=33,
                group=33,
            ),
            backup.ConcreteFile(
                "",
                f"SysContainerDomain-../../../../../../../../var/backup/var/containers/Bundle/Application/{app_uuid}/{app_name}/{app_name.split('.')[0]}",
                owner=33,
                group=33,
                contents=b"",
                inode=0,
            ),
            backup.ConcreteFile(
                "",
                "SysContainerDomain-../../../../../../../.." + "/crash_on_purpose", contents=b""),
        ]
    )

    try:
        perform_restore(back, reboot=False)
    except PyMobileDevice3Exception as e:
        if "Find My" in str(e):
            messagebox.showerror("Error", "Find My must be disabled in order to use this tool. Disable Find My and try again.")
            exit_app(1)
        elif "crash_on_purpose" not in str(e):
            raise e

    messagebox.showinfo("Info", "Rebooting device...")

    with DiagnosticsService(service_provider) as diagnostics_service:
        diagnostics_service.restart()

    messagebox.showinfo("Info", "Make sure to turn Find My iPhone back on after rebooting, and install a proper persistence helper after installing TrollStore!")


def on_replace_app():
    try:
        service_provider = LockdownClient()  # Connect to the device
        app_name = app_entry.get()
        if not app_name:
            messagebox.showwarning("Warning", "Please enter the name of the app.")
            return
        replace_app(service_provider, app_name)
    except NoDeviceConnectedError:
        messagebox.showerror("Error", "No device connected! Please connect your device and try again.")
        exit_app(1)
    except Exception:
        messagebox.showerror("Error", "An error occurred!\n" + traceback.format_exc())
        exit_app(1)


# def install_libraries():
#     try:
#         subprocess.run([sys.executable, "install.py"], check=True)
#         messagebox.showinfo("Success", "Libraries installed successfully. The application will now restart.")
#         python = sys.executable
#         os.execl(python, python, *sys.argv)
#     except subprocess.CalledProcessError:
#         messagebox.showerror("Error", "Failed to install libraries. Please try again.")


def main():
    root = tk.Tk()
    root.title("TrollRestore")

    tk.Label(root, text="Enter the app name to replace with TrollStore Helper:").pack(pady=10)
    global app_entry
    app_entry = tk.Entry(root, width=50)
    app_entry.pack(pady=5)

    replace_button = tk.Button(root, text="Install TrollStore", command=on_replace_app)
    replace_button.pack(pady=10)

    # install_lib_button = tk.Button(root, text="Install lib", command=install_libraries)
    # install_lib_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
