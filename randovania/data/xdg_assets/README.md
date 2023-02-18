## XDG Assets

These are the XDG assets for Randovania, used to create a desktop icon on Linux.

When installing manually, put the PNG in your icon database, for example:

```
cp io.github.randovania.Randovania.png ~/.local/share/icons/hicolor/256x256/apps/io.github.randovania.Randovania.png
```

The .desktop file can go in a similar location for app shortcuts:

```
cp io.github.randovania.Randovania.desktop ~/.local/share/applications/io.github.randovania.Randovania.desktop
```

Note that you will want to change the `Exec` line to match the path to your
local Randovania install. For example:

```
desktop-file-edit io.github.randovania.Randovania.desktop --set-key=Exec --set-value=/usr/local/bin/randovania
```
