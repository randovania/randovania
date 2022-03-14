# randovania-appimage

A set of build scripts to package [Randovania](https://github.com/randovania/randovania) up into an AppImage

## Usage

See the main Randovania README for Docker-based usage. The output image will be at:

```
out/Randovania-${randovania_git_ref}-amd64.AppImage"
```

## Non-Docker Usage

Clone the Randovania repo, `cd` into it, and invoke `tools/appimage/build.sh`. See the Dockerfile for build-time dependencies (all of them are). The builder user is not a requirement in non-Docker invocation.

**NOTE**: As part of the build process, the script will take your *system-wide Mono install* and bundle it into the application. Mono kinda has cross-compile environments, but they're fundamentally broken because they're missing completely random libraries. Be aware that the output AppImage will not be runnable by systems with a version of libc lower than yours!

The output AppImage will be at:

```
out/Randovania-${randovania_git_ref}-amd64.AppImage"
```

## Licensing

The build artifacts produced by this code contain code from other projects. Namely:

* We distribute Python. Python is licensed under the terms of the [Python Software Foundation License Agreement](https://docs.python.org/3/license.html#psf-license)
* We distribute Randovania. Randovania is licensed under [GPLv3](https://github.com/randovania/randovania/blob/main/LICENSE)
* We redistribute Mono as distributed by Canonical in the Ubuntu repositories. Mono is licensed under the terms of the [MIT License](https://github.com/mono/mono/blob/main/LICENSE)
* We obtain Newtonsoft.Json from NuGet. Newtonsoft.Json is licensed under the terms of the [MIT License](https://github.com/JamesNK/Newtonsoft.Json/blob/master/LICENSE.md). NuGet is not bundled in the output image.

## TODO

* Make the .desktop file in the AppImage actually point to randovania (maybe; I can't find another AppImage that actually implements this at all)
* Trim the heck out of the image, builds right now are like 200MB(!)
* Set up auto-update (and also figure out how to do so, docs say it's a thing)
 * https://github.com/AppImage/AppImageSpec/blob/master/draft.md#github-releases - Apparently it's a one-line configuration to get it to hook into GH releases
