# Shadow Threads Demo: Deterministic AI Coding Workflow

This repository demonstrates how Shadow Threads records and replays an AI-assisted coding workflow.

- deterministic AI refactor workflow
- artifact capture
- revision lineage
- execution replay verification

## Run the demo

```powershell
powershell .\demo-record.ps1
```

## What happens

- AI changes code
- tests fail
- revision history is shown
- execution is replayed
- replay is verified

## Requirements

- real Shadow Threads backend must already be running
- Python available
- PowerShell on Windows

## Main project

Shadow Threads core repository:
https://github.com/ZetongDu/shadow-threads