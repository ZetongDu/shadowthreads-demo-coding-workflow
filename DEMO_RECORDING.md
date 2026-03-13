# Shadow Threads Demo Recording Guide

## What this demo proves

This demo shows a realistic first-time developer workflow using Shadow Threads through the public Python SDK.

The story is:

1. AI changes code.
2. Tests fail.
3. Shadow Threads records revision lineage.
4. The failing execution boundary is recorded.
5. That execution boundary is replayed.
6. Replay is verified deterministically.

The demo is intentionally blackbox:

- it uses the real Shadow Threads backend
- it talks to Shadow Threads through `ShadowClient`
- it does not import server source modules
- it does not access Postgres or Redis directly

## Required environment setup

Before recording, make sure:

- Python is available on `PATH`
- the `shadowthreads` Python SDK is installed and importable
- this repository is opened at `C:\dev\shadowthreads-demo-coding-workflow`
- the real Shadow Threads backend is already running

The demo runner does not start the backend for you.

## How to start the real backend

Start the real Shadow Threads backend separately, using the normal backend startup flow for your Shadow Threads installation.

Default local URL:

```text
http://localhost:3001
```

If your backend is running elsewhere, set:

```powershell
$env:SHADOW_SERVER = "http://your-server:3001"
```

## How to run the demo

From the repository root:

```powershell
powershell .\demo-record.ps1
```

The script will:

1. check backend reachability through the Python SDK
2. reset local demo state
3. run the demo workflow

If the backend is unavailable, the script fails immediately with a clean message.

## Recommended terminal window size

Use a terminal size that keeps the full revision tree visible without wrapping.

Recommended:

- width: 120 to 140 columns
- height: 32 to 40 rows

## Recommended terminal font size

Recommended:

- font: Cascadia Mono, Consolas, or another clear monospace font
- font size: 18 pt to 20 pt

If the branch tree characters render poorly, switch to a font with strong Unicode box-drawing support.

## Suggested recording sequence

1. Open PowerShell in `C:\dev\shadowthreads-demo-coding-workflow`.
2. Confirm the terminal window is sized correctly.
3. Start screen recording.
4. Run:

   ```powershell
   powershell .\demo-record.ps1
   ```

5. Let the script complete without typing anything else.
6. Pause briefly on these moments during editing:
   - `Test failed`
   - `Revision history`
   - `Execution recorded`
   - `Replay verified: true`
7. End the clip on the final terminal state.

## Suggested subtitle text

Suggested subtitles, in order:

- `AI changed the code. The tests now fail.`
- `Shadow Threads records workflow state as deterministic revisions.`
- `The failing execution boundary is recorded and inspectable.`
- `Replay verifies the recorded execution deterministically.`

Final subtitle:

- `Shadow Threads - deterministic replay for AI workflows`

## Suggested freeze-frame ending

Freeze on the final terminal output showing:

- `Execution recorded: ...`
- `Replaying execution boundary`
- `Replay verified: true`

Hold the frame for 2 to 3 seconds with the final subtitle:

`Shadow Threads - deterministic replay for AI workflows`

## Troubleshooting steps

### Backend not reachable

Symptom:

```text
Shadow Threads server not reachable at http://localhost:3001
```

Fix:

- start the real backend first
- verify `SHADOW_SERVER` points to the correct backend URL

### Python SDK not importable

Symptom:

```text
Shadow Threads Python SDK not importable.
```

Fix:

- install the SDK in your current Python environment
- confirm `python -c "import shadowthreads"` works

### Demo output does not match the expected failure story

Symptom:

- tests pass unexpectedly
- revision history is incomplete

Fix:

- rerun `powershell .\demo-record.ps1`
- the script resets the local parser source before each run
- if the problem persists, confirm the repository contents were not manually edited

### Branch tree characters render incorrectly

Symptom:

- revision history tree lines look garbled

Fix:

- use Windows Terminal or another UTF-8 capable terminal
- switch to Cascadia Mono or Consolas
- keep the terminal encoding in UTF-8

### Recording is visually noisy

Fix:

- close other terminals or background tasks
- avoid resizing the terminal after recording starts
- do not scroll during the run
