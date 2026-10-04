$ErrorActionPreference = "Continue"

$projectRoot = Split-Path -Parent $PSScriptRoot
$docsDir = Join-Path $projectRoot "docs"
$python = (Get-Command python -ErrorAction Stop).Source
Set-Location $projectRoot

& $python main.py 2>&1 | Tee-Object -FilePath (Join-Path $docsDir "pipeline_run.log")
$pipelineExit = $LASTEXITCODE

& $python -m pytest -q 2>&1 | Tee-Object -FilePath (Join-Path $docsDir "pytest_run.log")
$pytestExit = $LASTEXITCODE

if ($pipelineExit -eq 0) {
    & $python -m scripts.inspect_outputs 2>&1 | Tee-Object -FilePath (Join-Path $docsDir "output_verification.log")
    $inspectionExit = $LASTEXITCODE
} else {
    "Skipped because pipeline exit code was $pipelineExit." | Set-Content (Join-Path $docsDir "output_verification.log")
    $inspectionExit = 1
}

@(
    "pipeline_exit=$pipelineExit"
    "pytest_exit=$pytestExit"
    "inspection_exit=$inspectionExit"
) | Set-Content (Join-Path $docsDir "validation_exit_codes.txt")

if (($pipelineExit -ne 0) -or ($pytestExit -ne 0) -or ($inspectionExit -ne 0)) {
    exit 1
}
