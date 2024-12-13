import platform
import sys
import traceback
from pathlib import Path

import click
import requests
from packaging.version import Version
from pymobiledevice3.cli.cli_common import Command
from pymobiledevice3.exceptions import NoDeviceConnectedError, PyMobileDevice3Exception
from pymobiledevice3.lockdown import LockdownClient
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3.services.installation_proxy import InstallationProxyService

from sparserestore import backup, perform_restore


def exit_with_prompt(code=0):
    """Exit gracefully, prompting the user on Windows."""
    if platform.system() == "Windows" and getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        input("Press Enter to exit...")
    sys.exit(code)


@click.command(cls=Command)
@click.pass_context
def cli(ctx, service_provider: LockdownClient) -> None:
    os_names = {
        "iPhone": "iOS",
        "iPad": "iPadOS",
        "iPod": "iOS",
        "AppleTV": "tvOS",
        "Watch": "watchOS",
        "AudioAccessory": "HomePod Software Version",
        "RealityDevice": "visionOS",
    }

    try:
        device_class = service_provider.get_value(key="DeviceClass")
        device_build = service_provider.get_value(key="BuildVersion")
        device_version = Version(service_provider.product_version)
    except (TypeError, ValueError):
        click.secho("Failed to get device information!", fg="red")
        click.secho("Make sure your device is connected and try again.", fg="red")
        return

    os_name = f"{os_names.get(device_class, '')} "
    unsupported_versions = (
        device_version < Version("15.0") or
        Version("16.7") < device_version < Version("17.0") or
        device_version > Version("17.0") or
        (device_version == Version("16.7") and device_build != "20H18")
    )

    if unsupported_versions:
        click.secho(f"{os_name}{device_version} ({device_build}) is not supported.", fg="red")
        click.secho("This tool is only compatible with iOS/iPadOS 15.0 - 16.7 RC and 17.0.", fg="red")
        return

    app_name = click.prompt(
        """
Please specify the removable system app you want to replace with TrollStore Helper.
If you don't know which app to specify, specify the Tips app.

Enter the app name""",
    ).strip()

    if not app_name.endswith(".app"):
        app_name += ".app"

    apps = InstallationProxyService(service_provider).get_apps(application_type="System", calculate_sizes=False)
    app_path = next(
        (
            Path(value["Path"]) for value in apps.values()
            if isinstance(value, dict) and value.get("Path") and Path(value["Path"]).name.lower() == app_name.lower()
        ),
        None
    )

    if not app_path:
        click.secho(f"Failed to find the removable system app '{app_name}'!", fg="red")
        return

    if Path("/private/var/containers/Bundle/Application") not in app_path.parents:
        click.secho(f"'{app_name}' is not a removable system app!", fg="red")
        return

    app_uuid = app_path.parent.name

    try:
        response = requests.get(
            "https://github.com/opa334/TrollStore/releases/latest/download/PersistenceHelper_Embedded",
            timeout=10
        )
        response.raise_for_status()
        helper_contents = response.content
    except requests.RequestException as e:
        click.secho(f"Failed to download TrollStore Helper: {e}", fg="red")
        return

    click.secho(f"Replacing {app_name} with TrollStore Helper. (UUID: {app_uuid})", fg="yellow")

    backup_files = [
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
            "SysContainerDomain-../../../../../../../../var/.backup.i/var/root/Library/Preferences/temp",
            owner=501,
            group=501,
            contents=b"",
        ),
        backup.ConcreteFile("", "SysContainerDomain-../../../../../../../../crash_on_purpose", contents=b""),
    ]

    try:
        perform_restore(backup.Backup(files=backup_files), reboot=False)
    except PyMobileDevice3Exception as e:
        if "Find My" in str(e):
            click.secho("Find My must be disabled in order to use this tool.", fg="red")
            exit_with_prompt(1)
        elif "crash_on_purpose" not in str(e):
            raise

    click.secho("Rebooting device", fg="green")

    with DiagnosticsService(service_provider) as diagnostics_service:
        diagnostics_service.restart()

    click.secho("Make sure you turn Find My iPhone back on if you use it after rebooting.", fg="green")
    click.secho("Make sure to install a proper persistence helper into the app you chose after installing TrollStore!", fg="green")


def main():
    try:
        cli(standalone_mode=False)
    except NoDeviceConnectedError:
        click.secho("No device connected!", fg="red")
        exit_with_prompt(1)
    except click.UsageError as e:
        click.secho(e.format_message(), fg="red")
        click.echo(cli.get_help(click.Context(cli)))
        exit_with_prompt(2)
    except Exception:
        click.secho("An error occurred!", fg="red")
        click.secho(traceback.format_exc(), fg="red")
        exit_with_prompt(1)

    exit_with_prompt(0)


if __name__ == "__main__":
    main()
