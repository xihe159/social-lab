param(
    [string]$Backend = "",
    [int]$Port = 0
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

$argsList = @("$ScriptDir\run_phase12_uvicorn_smoke.py")
if ($Backend) {
    $argsList += @("--backend", $Backend)
}
if ($Port -gt 0) {
    $argsList += @("--port", "$Port")
}

& python @argsList
exit $LASTEXITCODE
