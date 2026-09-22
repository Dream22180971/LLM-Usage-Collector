$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$date = Get-Date -Format "yyyy-MM-dd"
$outDir = Join-Path $root "reports"
if (!(Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$outFile = Join-Path $outDir "daily_$date.json"
& python (Join-Path $root "main.py") --json --days 30 | Out-File -FilePath $outFile -Encoding utf8
Write-Host "Report saved: $outFile"
