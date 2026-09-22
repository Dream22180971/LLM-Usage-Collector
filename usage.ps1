$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
& python (Join-Path $root "main.py") @args
exit $LASTEXITCODE
