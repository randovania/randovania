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

# The string to feed to gh-releases-zsync, which is used for automatic AppImage
# update delivery.
# TODO: Add two of these and pick one based on whether this is a devel or
#       stable release
zsync_prod_string="gh-releases-zsync|randovania|randovania|latest|Randovania*$(uname -m).AppImage.zsync"

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
mono_mkbundle_args="-v --simple --static --machine-config /etc/mono/4.5/machine.config --no-config --deps"
# We include liblzo2 because it's unlikely to be available on the host at the
# path Mono expects
mono_mkbundle_args="$mono_mkbundle_args --library $(ldconfig -p | grep 'liblzo2.so' | head -n 1 | awk '{print $4}' | xargs readlink -f)"
# We include libmono-native.so explicitly as some distro configs are set up
# such that mkbundle --static will not automatically pull it in
mono_mkbundle_args="$mono_mkbundle_args --library $(ldconfig -p | grep 'libmono-native.so' | head -n 1 | awk '{print $4}' | xargs readlink -f)"
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

build-copy-randovania-into-image() {
	# Create a directory in the working squashfs-root and sync the source tree
	# into it.
	mkdir -p squashfs-root/"$randovania_location"
	rsync -a ../dist/randovania/ squashfs-root/"$randovania_location"
}
build-copy-overlay-into-image() {
	# Copy the overlay (which contains AppImage and Linux-specific files) into the
	# working squashfs-root
	rsync -a --no-owner --no-group ../tools/appimage/overlay/ squashfs-root/
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
	pushd squashfs-root/"$randovania_location"/data/ClarisEchoesMenu
	mkbundle $mono_mkbundle_args --config EchoesMenu.exe.config EchoesMenu.exe -o echoes-menu
	popd

	# Randomizer.exe
	# This one is slightly more complex, as we have to add several dependencies
	# via nuget.exe since they're either third-party or just straight up not
	# included in the cross-compile runtimes for some reason
	mono /usr/local/lib/nuget.exe install NewtonSoft.json -OutputDirectory nuget
	#mono nuget.exe install Novell.Directory.Ldap -OutputDirectory nuget
	nugetdir="$PWD/nuget"
	pushd squashfs-root/"$randovania_location"/data/ClarisPrimeRandomizer/
	mkbundle $mono_mkbundle_args --config Randomizer.exe.config Randomizer.exe -o randomizer \
		-L "$nugetdir"/Newtonsoft.Json.*/lib/net45 \
		-L "$nugetdir"/Novell.Directory.Ldap.*/lib
	popd
}
build-appimage-meta() {
	# Build AppImage metainfo
	# TODO: That
	metadir="squashfs-root/usr/share/metainfo"
	metainfo="$metadir/org.randovania.randovania.appdata.xml"
	mkdir -p "$metadir"
	cat ../tools/appimage/metainfo-head.xml > "$metainfo"
	sed ../README.md -ne '/<!-- Begin WELCOME -->/, /<!-- End WELCOME -->/p' | head -n -1 | tail -n +2 | markdown >> "$metainfo"
	cat ../tools/appimage/metainfo-tail.xml >> "$metainfo"
}
build-compile-image() {
	# Build the squashfs-root into an AppImage
	# This also automatically creates a .zsync file that we will want to bundle
	# with the GitHub release.
	appimagetool squashfs-root -u "$zsync_prod_string" ../"$outdir"/"Randovania-$(uname -m).AppImage"
	mv *.zsync ../"$outdir"/
}

main() {
	# Set debugging mode from here on
	set -x

	setup-build-env
	setup-activate-env

	build-copy-overlay-into-image
	build-copy-randovania-into-image
	build-static-mono
	build-appimage-meta
	build-compile-image
}
main "$@"
