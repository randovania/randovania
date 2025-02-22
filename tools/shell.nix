# Development shell environment for Randovania on Nix.
#
# This will:
# - create the venv and install all requirements, if it doesn't already exist
# - set up $LD_LIBRARY_PATH with the system libraries needed for RDV
# - define $RANDOVANIA_PATH as the root of the RDV source checkout
# - define `rdv` as a shell function that runs RDV from the source root
#
# So, basic usage is:
# $ nix-shell tools/shell.nix
# [...long wait while it installs requirements, if this is the first time]
# [...do some coding...]
# $ rdv
#
# Or, if you just want to run rdv as a one-off:
# $ nix-shell tools/shell.nix --run rdv

{ pkgs ? import <nixpkgs> {} }:

let
  libs = with pkgs; [
    dbus
    fontconfig
    freetype
    glib
    libgcc.lib
    libGL
    libxkbcommon
    libz
    wayland
    xcb-util-cursor
    xorg.libxcb
    xorg.xcbutilimage
    xorg.xcbutilkeysyms
    xorg.xcbutilrenderutil
    xorg.xcbutilwm
    xorg.libX11
    zstd
  ];
in pkgs.mkShell {
  name = "randovania-dev-shell";

  packages = with pkgs; [
    fontconfig
    python312
    python312Packages.pip
  ];

  shellHook = ''
    cd "${toString ./..}" || exit 1
    [[ -f randovania.spec ]] || exit 1

    # This is very expensive, so only do it if the venv doesn't already exist.
    # If the user needs to regenerate the venv, they can delete it.
    if ! [[ -d venv ]]; then
      tools/prepare_virtual_env.sh
      (
        source venv/bin/activate
        python -m pip install -r requirements.txt
      )
    fi

    export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath libs}:$LD_LIBRARY_PATH"
    export RANDOVANIA_PATH="$PWD"

    function rdv {
      (cd "$RANDOVANIA_PATH" && tools/start_client.sh)
    }
  '';
}
