$ErrorActionPreference = "Stop"

$version = "3.4.1"
$expectedSha256 = "aa8098a433e6d63b865074468aa2da1aa9329ef33c9e9af799037f382ce50b82"
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimeRoot = Join-Path $projectRoot ".hadoop"
$archive = Join-Path $runtimeRoot "hadoop-$version.zip"
$destination = Join-Path $runtimeRoot "hadoop-$version"
$releaseUrl = "https://github.com/zehelh/winutils/releases/download/hadoop-$version/hadoop-$version.zip"

if (Test-Path (Join-Path $destination "bin\winutils.exe")) {
    Write-Host "Hadoop $version Windows runtime already exists at $destination"
    exit 0
}

New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
Invoke-WebRequest -Headers @{ "User-Agent" = "NYC-Taxi-Data-Engineering-Setup" } `
    -Uri $releaseUrl -OutFile $archive

$actualSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
if ($actualSha256 -ne $expectedSha256) {
    Remove-Item -LiteralPath $archive -Force
    throw "SHA-256 mismatch for $releaseUrl. Expected $expectedSha256, got $actualSha256."
}

Expand-Archive -LiteralPath $archive -DestinationPath $runtimeRoot -Force
Remove-Item -LiteralPath $archive -Force
Write-Host "Installed Hadoop $version Windows runtime at $destination"
