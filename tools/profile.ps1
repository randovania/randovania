
$permalink = "rvf77/QDgKA="
$app = Start-Process -FilePath python -ArgumentList "-m randovania echoes distribute $permalink seed.rdvgame" -passthru -NoNewWindow
py-spy record -o profile.svg --subprocesses --pid $app.Id