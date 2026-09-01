$ErrorActionPreference = 'Stop'
$installer = Join-Path $PSScriptRoot 'install.py'
$candidates = @(
    @{ Name = 'py'; Prefix = @('-3') },
    @{ Name = 'python3'; Prefix = @() },
    @{ Name = 'python'; Prefix = @() }
)
foreach ($candidate in $candidates) {
    $command = Get-Command $candidate.Name -ErrorAction SilentlyContinue
    if (-not $command) { continue }
    & $command.Source @($candidate.Prefix) -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' *> $null
    if ($LASTEXITCODE -eq 0) {
        & $command.Source @($candidate.Prefix) $installer @args
        exit $LASTEXITCODE
    }
}
throw 'Python 3.11 or newer is required.'
