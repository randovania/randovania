import subprocess

from randovania import monitoring
from randovania.patching.patchers.exceptions import UnableToExportError


class DotnetNotSetupException(UnableToExportError):
    def __init__(self, reason: str):
        super().__init__(reason)


def is_dotnet_set_up() -> None:
    """Checks if dotnet is set up. Throws a DotnetNotSetupException exception if it's not the case."""

    try:
        dotnet_process = subprocess.run(["dotnet", "--info"], check=False)
        dotnet_ran_fine = dotnet_process.returncode == 0
    except FileNotFoundError:
        dotnet_ran_fine = False

    monitoring.set_tag("dotnet_ran_fine", dotnet_ran_fine)
    if not dotnet_ran_fine:
        raise DotnetNotSetupException(
            "You do not have .NET installed!\n"
            "Please ensure that it is installed and located in PATH. It can be installed "
            "from here:\n"
            "https://aka.ms/dotnet/download"
        )
