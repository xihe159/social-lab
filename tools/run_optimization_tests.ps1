param(
    [string]$FromPhase = "00",
    [string]$ToPhase = "09",
    [switch]$ContinueOnFailure
)

$ArgsList = @(
    "tools/run_optimization_tests.py",
    "--from-phase", $FromPhase,
    "--to-phase", $ToPhase
)

if ($ContinueOnFailure) {
    $ArgsList += "--continue-on-failure"
}

python @ArgsList
exit $LASTEXITCODE
