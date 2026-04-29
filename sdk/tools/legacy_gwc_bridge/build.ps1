param(
  [string]$Configuration = "Release"
)

$ErrorActionPreference = "Stop"
$Project = Join-Path $PSScriptRoot "LegacyGwcBridge.csproj"
dotnet build $Project -c $Configuration
