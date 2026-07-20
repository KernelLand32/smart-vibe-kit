#Requires -Version 5.1
<#
.SYNOPSIS
  Cross-platform Smart Vibe Kit installer (Windows wrapper → install.py).
.DESCRIPTION
  Installs into Cursor, Claude Code, Codex, Gemini CLI, and the shared
  ~/.agents/skills path. Prefer: python scripts/install.py …
.EXAMPLE
  .\scripts\install.ps1
  .\scripts\install.ps1 -Target agents -Scope user
  .\scripts\install.ps1 -Target all -Scope project -ProjectRoot .
  .\scripts\install.ps1 -List
  .\scripts\install.ps1 -Uninstall -Target cursor
#>
param(
    [ValidateSet("all", "agents", "cursor", "claude", "codex", "gemini")]
    [string]$Target = "all",
    [ValidateSet("user", "project")]
    [string]$Scope = "user",
    [string]$ProjectRoot = (Get-Location).Path,
    [switch]$AlsoLegacyClaudeCommand,
    [switch]$WhatIf,
    [switch]$NoBackup,
    [switch]$Link,
    [switch]$List,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$ScriptDir = $PSScriptRoot
$InstallPy = Join-Path $ScriptDir "install.py"

function Find-Python {
    foreach ($cand in @(
        @{ File = "py"; Args = @("-3") },
        @{ File = "python3"; Args = @() },
        @{ File = "python"; Args = @() }
    )) {
        $cmd = Get-Command $cand.File -ErrorAction SilentlyContinue
        if ($cmd) {
            return @{ Exe = $cmd.Source; Prefix = $cand.Args }
        }
    }
    return $null
}

$py = Find-Python
if (-not $py) {
    Write-Error "Python 3 is required. Install from https://www.python.org/downloads/ then re-run."
}

$argv = @($InstallPy)
if ($List) {
    $argv += "--list"
} else {
    $argv += @("--target", $Target, "--scope", $Scope, "--project-root", $ProjectRoot)
    if ($AlsoLegacyClaudeCommand) { $argv += "--also-legacy-claude-command" }
    if ($WhatIf) { $argv += "--what-if" }
    if ($NoBackup) { $argv += "--no-backup" }
    if ($Link) { $argv += "--link" }
    if ($Uninstall) { $argv += "--uninstall" }
}

$allArgs = @($py.Prefix) + $argv
Write-Host ("→ {0} {1}" -f $py.Exe, ($allArgs -join " "))
& $py.Exe @allArgs
exit $LASTEXITCODE
