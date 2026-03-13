$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = $ScriptDir
$PythonExe = "python"
$ServerUrl = if ($env:SHADOW_SERVER) { $env:SHADOW_SERVER } else { "http://localhost:3001" }

[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:SHADOW_SERVER = $ServerUrl

function Fail([string]$Message) {
    Write-Host $Message
    exit 1
}

function Invoke-PythonFromStdin([string]$Code) {
    $Code | & $PythonExe - 2>&1 | ForEach-Object { Write-Host $_ }
    $exitCode = $LASTEXITCODE
    return $exitCode
}

function Invoke-BackendPreflight {
    $code = @'
import os
import sys

server = os.getenv("SHADOW_SERVER", "http://localhost:3001")

try:
    from shadowthreads import ShadowClient
except Exception:
    print("Shadow Threads Python SDK not importable.")
    print("Install the SDK before recording this demo.")
    raise SystemExit(1)

client = ShadowClient(base_url=server)
try:
    client.list_revisions("shadowthreads-demo-coding-workflow", limit=1)
except Exception:
    print(f"Shadow Threads server not reachable at {client.base_url}")
    print("Please start the real backend before recording this demo.")
    raise SystemExit(1)
finally:
    close = getattr(client, "close", None)
    if callable(close):
        close()

print(f"Backend reachable: {client.base_url}")
'@

    $exitCode = Invoke-PythonFromStdin -Code $code
    if ($exitCode -ne 0) {
        exit $exitCode
    }
}

function Reset-DemoState {
    $code = @'
from pathlib import Path

from src.refactor_engine import BASELINE_SOURCE

root = Path.cwd()
parser_path = root / "src" / "parser.py"
artifacts_dir = root / "artifacts"
artifacts_dir.mkdir(parents=True, exist_ok=True)

parser_path.write_text(BASELINE_SOURCE, encoding="utf-8")

for name in (
    "workflow_input.json",
    "baseline_source.json",
    "refactor_plan.json",
    "refactored_source.json",
    "code_patch.json",
    "test_report.json",
):
    path = artifacts_dir / name
    if path.exists():
        path.unlink()

print("Demo state reset.")
'@

    $exitCode = Invoke-PythonFromStdin -Code $code
    if ($exitCode -ne 0) {
        Fail "Failed to reset local demo state."
    }
}

Push-Location $RepoRoot
try {
    Write-Host "Shadow Threads demo runner"
    Invoke-BackendPreflight
    Reset-DemoState
    Write-Host ""

    & $PythonExe "run_workflow.py"
    if ($LASTEXITCODE -ne 0) {
        Fail "Demo workflow failed."
    }
}
finally {
    Pop-Location
}
