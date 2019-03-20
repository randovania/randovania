from PyInstaller.utils.hooks import collect_data_files

# See https://github.com/pyinstaller/pyinstaller/issues/4040

datas = collect_data_files('shiboken2', include_py_files=True, subdir='support')
