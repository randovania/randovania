from __future__ import annotations

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

datas = collect_data_files("keystone")
binaries = collect_dynamic_libs("keystone")
