# Shadow Threads Coding Workflow Demo

This demo shows a minimal AI-assisted coding workflow where a parser refactor introduces a subtle regression, and Shadow Threads makes the failure traceable.

## Scenario

The workflow starts from a baseline parser that:

- parses comma-separated integers
- strips surrounding whitespace
- ignores empty tokens

The simulated AI refactor proposes a reasonable change: strip tokens before parsing. The bug is not a trivial typo. The refactor introduces an in-place normalization helper that mutates the shared token list and checks emptiness against the stale pre-strip value. For the input `"1, 2, , 4"`, the whitespace-only token is mutated into `""` but never removed, so parsing later fails with `ValueError`.

Without Shadow Threads, the team sees a failing test and a modified file. The workflow step that introduced the state mutation is easy to miss.

With Shadow Threads, the demo records:

- explicit task state as artifacts
- revision lineage from baseline to mutated parser to post-refactor failure state
- the failed execution boundary
- deterministic replay verification for that execution

## Recorded Lineage

The workflow creates three revisions:

- `R1`: `baseline parser state`
- `R2`: `AI refactor mutated parser state`
- `R3`: `post-refactor failing test result`

`R2` carries the baseline source reference forward alongside the refactor plan, refactored source, and patch artifact. `R3` attaches the failing test report directly to the refactored source so the failure is clearly tied to the mutated code state.

## Files

- [src/parser.py](c:/dev/shadowthreads-demo-coding-workflow/src/parser.py): baseline parser implementation
- [src/refactor_engine.py](c:/dev/shadowthreads-demo-coding-workflow/src/refactor_engine.py): deterministic simulated AI refactor
- [src/workflow_engine.py](c:/dev/shadowthreads-demo-coding-workflow/src/workflow_engine.py): Shadow Threads integration and workflow orchestration
- [tests/test_parser.py](c:/dev/shadowthreads-demo-coding-workflow/tests/test_parser.py): parser tests, including the empty-token case
- [run_workflow.py](c:/dev/shadowthreads-demo-coding-workflow/run_workflow.py): CLI entrypoint

## Run

Prerequisites:

- Python can import the `shadowthreads` SDK.
- A real Shadow Threads server is running at `http://localhost:3001`, or `SHADOW_SERVER` points to the real backend.

From the project root:

```bash
python run_workflow.py
```

The workflow talks only to the real Shadow Threads backend through the Python SDK. If the backend is unavailable, the script exits immediately with:

```text
Shadow Threads server not reachable at http://localhost:3001
Please start the backend service before running this workflow.
```

The CLI prints a compact workflow story:

```text
Loading source code
Generating AI refactor plan
Applying code modification
Producing patch artifact
Running tests

Test failed

Revision history
R3 post-refactor failing test result
└─ R2 AI refactor mutated parser state
   └─ R1 baseline parser state

Execution recorded: <execution_id>
Replaying execution boundary
Replay verified: true
```

Local artifact payloads are written into `artifacts/` using the required names: `workflow_input`, `baseline_source`, `refactor_plan`, `refactored_source`, `code_patch`, and `test_report`. The workflow restores `src/parser.py` to the baseline source in `finally` and verifies the restore before exiting, so reruns stay deterministic.
