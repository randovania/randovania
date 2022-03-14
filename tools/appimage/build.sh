#! /bin/bash
#
# build.sh
# Builds Randovania into an AppImage
#
# This script is mostly built on this guide from AppImageKit:
# https://github.com/AppImage/AppImageKit/wiki/Bundling-Python-apps
#
# Copyright (C) 2022 Salt <jacob@babor.tech>
# Distributed under terms of the GNU General Public License, Version 3
#

set -e

#
# Configuration vars
# These variables can be freely modified
#

# The URL to the Python AppImage we'll bundle RDV in
python_appimage="https://github.com/niess/python-appimage/releases/download/python3.9/python3.9.10-cp39-cp39-manylinux1_x86_64.AppImage"
# The URL to appimagetool, used to build the final image
appimagetool_appimage="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
# The URL to nuget, which is used to fetch Mono libraries as needed
nuget_url="https://dist.nuget.org/win-x86-commandline/latest/nuget.exe"

#
# Extra vars
# These should not be modified just for build configuration
#

# The directory where temporary AppImage files live, relative to the repo root
# Must not be a subdirectory
workdir="work"
# The directory where the output AppImage is built, relative to the repo root
# Must not be a subdirectory
outdir="out"

# These arguments tell Mono to build a static binary
mono_mkbundle_args="-v --simple --static --no-machine-config --no-config --deps"
# We include liblzo2 because it's unlikely to be available on the host at the
# path Mono expects
mono_mkbundle_args="$mono_mkbundle_args --library $(ldconfig -p | grep 'liblzo2.so' | head -n 1 | awk '{print $4}')"
# We include libmono-native.so explicitly as some distro configs are set up
# such that mkbundle --static will not automatically pull it in
mono_mkbundle_args="$mono_mkbundle_args --library $(ldconfig -p | grep 'libmono-native.so' | head -n 1 | awk '{print $4}')"
# Include Host libraries
mono_mkbundle_args="$mono_mkbundle_args -L /usr/lib/mono/4.5"
# The location of Randovania within the AppImage
# NOTE: This is referred to in external files as well!
randovania_location="/opt/randovania"

setup-build-env() {
	# Setup a directory tree and perform any minor tweaks we may need to make to
	# ensure we can build our image.
	mkdir -p "$workdir"
	mkdir -p "$outdir"
}
setup-activate-env() {
	# cd into our build environment
	pushd "$workdir"
}

build-obtain-appimagetool() {
	# Obtain the version of appiamgetool we need to build the AppImage
	wget "$appimagetool_appimage"
	chmod +x appimagetool*.AppImage
	# Extract AIT
	# We have to do this because Docker build systems won't let us use FUSE to
	# actually run the appimage normally.
	./appimagetool-x86_64.AppImage --appimage-extract
	mv squashfs-root appimagetool
}
build-obtain-python() {
	# Obtain the version of Python we need to build Randovania
	# This extracst the image to ./squashfs-root
	wget "$python_appimage"
	chmod +x python*-manylinux1_x86_64.AppImage
	./python*-manylinux1_x86_64.AppImage --appimage-extract
}
build-obtain-nuget() {
	# Obtain the version of nuget we need to grab Mono app dependencies
	wget "$nuget_url"
	mkdir -p nuget
}
build-copy-randovania-into-image() {
	# Create a directory in the working squashfs-root and sync the source tree
	# into it.
	mkdir -p squashfs-root/"$randovania_location"
	rsync -a --exclude={"$workdir"/,"$outdir"/} ../ squashfs-root/"$randovania_location"
}
build-copy-overlay-into-image() {
	# Copy the overlay (which contains AppImage and Linux-specific files) into the
	# working squashfs-root
	rsync -a ../tools/appimage/overlay/ squashfs-root/
}
build-static-mono() {
	# Bundle up our Mono apps to avoid having to redistribute the Mono runtime
	# This depends on a few things on the host:
	#
	#  - Libraries liblzo2 and libmono-native must both be present
	#
	#  - The .config files that add a dllmap for liblzo2 are required at build time
	#    (this step is handled by copying in the overlay above)
	#
	#  - The host has to have mono-complete installed (package name is a debianism,
	#    but the long and short of it is that you need the full runtime and dev
	#    tooling
	#
	#  - The host has to have a libc version <= that of the oldest version we're
	#    willing to support.
	#
	# If all goes well, you'll get a static binary that runs on anything, no Mono
	# runtime required. No futzing with liblzo2 required. Just Werks.

	# EchoesMenu.exe
	pushd squashfs-root/"$randovania_location"/randovania/data/ClarisEchoesMenu
	mkbundle $mono_mkbundle_args --config EchoesMenu.exe.config EchoesMenu.exe -o echoes-menu
	popd

	# Randomizer.exe
	# This one is slightly more complex, as we have to add several dependencies
	# via nuget.exe since they're either third-party or just straight up not
	# included in the cross-compile runtimes for some reason
	mono nuget.exe install NewtonSoft.json -OutputDirectory nuget
	#mono nuget.exe install Novell.Directory.Ldap -OutputDirectory nuget
	nugetdir="$PWD/nuget"
	pushd squashfs-root/"$randovania_location"/randovania/data/ClarisPrimeRandomizer/
	mkbundle $mono_mkbundle_args --config Randomizer.exe.config Randomizer.exe -o randomizer \
		-L "$nugetdir"/Newtonsoft.Json.*/lib/net45 \
		-L "$nugetdir"/Novell.Directory.Ldap.*/lib
	popd
}
build-install-randovania() {
	# Enter the Randovania directory inside squashfs-root and install its
	# dependencies. We avoid activating the venv here because the Python
	# interpreter in the AppImage we extracted already has a pseudo-venv going on
	# with respect to the AppImage root.
	pushd squashfs-root/"$randovania_location"
	# Install dependencies
	python -m pip install --upgrade -r requirements-setuptools.txt
	python -m pip install -e . -e ".[gui]"
	# Workaround for #2968
	python -m pip install pyqt-distutils
	python setup.py build_ui
	# I'm not building a whole release just to get this one json file lol
	cat > randovania/data/configuration.json <<- EOF
	{"discord_client_id": 618134325921316864, "server_address": "https://randovania.metroidprime.run/randovania", "socketio_path": "/randovania/socket.io"}
	EOF
	popd
}
build-thin-image() {
	# Note: this step does not "build a thin image", it's a build step that "thins
	# the image". This removes some large cruft that we don't hard depend on so we
	# can lower the size of the distributed AppImage
	# Remove configuration from the upstream python AppImage
	rm \
		squashfs-root/usr/share/applications/python*.desktop \
		squashfs-root/usr/share/icons/hicolor/256x256/apps/python*.png \
		squashfs-root/usr/share/metainfo/python*.appdata.xml \
		squashfs-root/python*.desktop \
		squashfs-root/python*.png
	# Trim the fat
	rm -rf \
		squashfs-root/opt/randovania/.git* \
		squashfs-root/opt/randovania/pylintrc \
		squashfs-root/opt/randovania/requirements* \
		squashfs-root/opt/randovania/setup.cfg \
		squashfs-root/opt/randovania/venv/lib/python3.9/site-packages/PySide2/Qt/lib/libQt5WebEngineCore.so.5 \
		squashfs-root/opt/randovania/venv/lib/python3.9/site-packages/PySide2/Qt/translations/qtwebengine_locales
}
build-compile-image() {
	# Build the squashfs-root into an AppImage
	./appimagetool/AppRun squashfs-root ../"$outdir"/"Randovania-$randovania_git_ref-amd64.AppImage"
}


main() {
	# Set debugging mode from here on
	set -x

	setup-build-env
	setup-activate-env

	build-obtain-appimagetool
	build-obtain-python
	build-obtain-nuget

	# We add squashfs-root to PATH here so we can leverage this particular python
	# install instead of the system-wide one
	export PATH="$PWD"/squashfs-root/usr/bin:"$PATH"

	build-copy-overlay-into-image
	build-copy-randovania-into-image
	build-static-mono
	build-install-randovania

	build-thin-image
	build-compile-image
}
main "$@"
