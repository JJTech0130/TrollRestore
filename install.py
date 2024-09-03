import subprocess
import os
import time
import sys

# Danh sách các gói cần cài đặt
packages = [
    "pymobiledevice3", "bpylist2", "rich", "requests", "click"
]


def update_pip_and_path():
    current_path = os.getcwd()
    subprocess.check_call(["curl", "https://bootstrap.pypa.io/get-pip.py", "-o", "get-pip.py"])
    subprocess.check_call([sys.executable, "get-pip.py"])

    user_home = os.path.expanduser('~')
    new_path = os.path.join(user_home, 'AppData', 'Local', 'Programs', 'Python', 'Python312', 'Scripts')
    os.environ['PATH'] += os.pathsep + new_path

def install_if_missing(package):
    try:
        __import__(package)
        print(f"{package} is already installed.")
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"{package} has been installed.")

def update_system_path(new_path):
    subprocess.check_call(['setx', 'PATH', f"%PATH%;{new_path}", '/M'])

def main():
    # Install necessary libraries
    for package in packages:
        install_if_missing(package)

    class color:
        PURPLE = '\033[95m'
        CYAN = '\033[96m'
        DARKCYAN = '\033[36m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'
        END = '\033[0m'

    print(f"{color.BOLD + color.RED}Updating pip and configuring path...{color.END}")
    update_pip_and_path()

    print(f"{color.BOLD + color.RED}Installation complete!{color.END}")

if __name__ == "__main__":
    main()
