"""Workflow orchestration for the Shadow Threads coding demo."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from shadowthreads import ArtifactReference, RevisionMetadata, ShadowClient
from shadowthreads.errors import ShadowThreadsError

from src.refactor_engine import SIMULATED_PROMPT, apply_refactor, generate_refactor_plan


ROOT_DIR = Path(__file__).resolve().parents[1]
PARSER_PATH = ROOT_DIR / "src" / "parser.py"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
PACKAGE_ID = "shadowthreads-demo-coding-workflow"
TEST_COMMAND = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]
TEST_COMMAND_DISPLAY = "python -m unittest discover -s tests -v"
BASE_TIME = datetime(2026, 3, 12, 0, 0, tzinfo=UTC)


@dataclass
class StoredArtifact:
    name: str
    path: Path
    bundle_hash: str


@dataclass
class WorkflowRunResult:
    workflow_status: str
    failure_reason: str | None
    bundle_hashes: dict[str, str]
    revision_hashes: dict[str, str]
    execution_id: str | None
    replay_verified: bool | None
    artifact_paths: dict[str, str]
    restore_verified: bool


def run_workflow() -> WorkflowRunResult:
    client = create_shadow_client()
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    original_source = PARSER_PATH.read_text(encoding="utf-8")
    stored_artifacts: dict[str, StoredArtifact] = {}
    revision_hashes: dict[str, str] = {}
    execution_id: str | None = None
    replay_verified: bool | None = None
    workflow_status = "failure"
    failure_reason: str | None = None
    result: WorkflowRunResult | None = None
    restore_verified = False

    try:
        print("Loading source code")
        workflow_input = {
            "task": "refactor parser",
            "source_file": "src/parser.py",
            "test_command": TEST_COMMAND_DISPLAY,
        }
        stored_artifacts["workflow_input"] = capture_artifact(
            client=client,
            name="workflow_input",
            schema="coding.workflow.input",
            payload=workflow_input,
        )
        stored_artifacts["baseline_source"] = capture_artifact(
            client=client,
            name="baseline_source",
            schema="coding.workflow.source",
            payload={
                "file": "src/parser.py",
                "state": "baseline",
                "source": original_source,
            },
        )
        revision_hashes["R1"] = create_revision(
            client=client,
            artifacts=[
                ArtifactReference(
                    bundle_hash=stored_artifacts["workflow_input"].bundle_hash,
                    role="workflow_input",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["baseline_source"].bundle_hash,
                    role="baseline_source",
                ),
            ],
            message="baseline parser state",
            source="human",
            timestamp=timestamp_for(0),
        )

        print("Generating AI refactor plan")
        plan = generate_refactor_plan(original_source)
        stored_artifacts["refactor_plan"] = capture_artifact(
            client=client,
            name="refactor_plan",
            schema="coding.workflow.refactor_plan",
            payload=plan,
        )

        print("Applying code modification")
        refactor_result = apply_refactor(original_source, plan)
        PARSER_PATH.write_text(refactor_result.refactored_source, encoding="utf-8")
        stored_artifacts["refactored_source"] = capture_artifact(
            client=client,
            name="refactored_source",
            schema="coding.workflow.source",
            payload={
                "file": "src/parser.py",
                "state": "post_refactor",
                "source": refactor_result.refactored_source,
            },
            references=[
                ArtifactReference(
                    bundle_hash=stored_artifacts["baseline_source"].bundle_hash,
                    role="baseline_source",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["refactor_plan"].bundle_hash,
                    role="refactor_plan",
                ),
            ],
        )

        print("Producing patch artifact")
        stored_artifacts["code_patch"] = capture_artifact(
            client=client,
            name="code_patch",
            schema="coding.workflow.patch",
            payload=refactor_result.patch_payload,
            references=[
                ArtifactReference(
                    bundle_hash=stored_artifacts["baseline_source"].bundle_hash,
                    role="baseline_source",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["refactored_source"].bundle_hash,
                    role="refactored_source",
                ),
            ],
        )

        revision_hashes["R2"] = create_revision(
            client=client,
            artifacts=[
                ArtifactReference(
                    bundle_hash=stored_artifacts["baseline_source"].bundle_hash,
                    role="baseline_source",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["refactor_plan"].bundle_hash,
                    role="refactor_plan",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["refactored_source"].bundle_hash,
                    role="refactored_source",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["code_patch"].bundle_hash,
                    role="code_patch",
                ),
            ],
            message="AI refactor mutated parser state",
            source="ai",
            timestamp=timestamp_for(1),
            parent_revision_hash=revision_hashes["R1"],
        )

        print("Running tests")
        test_run = subprocess.run(
            TEST_COMMAND,
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            check=False,
        )
        test_report_payload = build_test_report(test_run)
        stored_artifacts["test_report"] = capture_artifact(
            client=client,
            name="test_report",
            schema="coding.workflow.test_report",
            payload=test_report_payload,
            references=[
                ArtifactReference(
                    bundle_hash=stored_artifacts["refactored_source"].bundle_hash,
                    role="refactored_source",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["code_patch"].bundle_hash,
                    role="code_patch",
                ),
            ],
        )
        if test_run.returncode == 0:
            raise RuntimeError("Expected post-refactor tests to fail, but they passed.")
        print("")
        print("Test failed")

        revision_hashes["R3"] = create_revision(
            client=client,
            artifacts=[
                ArtifactReference(
                    bundle_hash=stored_artifacts["refactored_source"].bundle_hash,
                    role="refactored_source",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["test_report"].bundle_hash,
                    role="test_report",
                ),
            ],
            message="post-refactor failing test result",
            source="system",
            timestamp=timestamp_for(2),
            parent_revision_hash=revision_hashes["R2"],
        )

        execution = client.record_execution(
            package_id=PACKAGE_ID,
            revision_hash=revision_hashes["R3"],
            provider="shadowthreads-demo",
            model="simulated-refactor-engine",
            prompt_hash=hash_prompt(SIMULATED_PROMPT),
            parameters={
                "change": plan["change"],
                "test_command": TEST_COMMAND_DISPLAY,
            },
            input_artifacts=[
                ArtifactReference(
                    bundle_hash=stored_artifacts["refactor_plan"].bundle_hash,
                    role="refactor_plan",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["refactored_source"].bundle_hash,
                    role="refactored_source",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["code_patch"].bundle_hash,
                    role="code_patch",
                ),
            ],
            output_artifacts=[
                ArtifactReference(
                    bundle_hash=stored_artifacts["refactored_source"].bundle_hash,
                    role="refactored_source",
                ),
                ArtifactReference(
                    bundle_hash=stored_artifacts["test_report"].bundle_hash,
                    role="test_report",
                ),
            ],
            status="failure",
            started_at=timestamp_for(3),
            finished_at=timestamp_for(4),
        )
        execution_id = execution.execution_id
        print("")
        print("Revision history")
        lineage_lines = format_revision_history(client, revision_hashes)
        for line in lineage_lines:
            print(line)
        print("")
        print(f"Execution recorded: {execution_id}")

        print("Replaying execution boundary")
        replay = client.replay_execution(execution.execution_id)
        replay_verified = replay.verified
        print(f"Replay verified: {str(replay.verified).lower()}")

        workflow_status = "failure"
        failure_reason = test_report_payload.get("summary")
        result = WorkflowRunResult(
            workflow_status=workflow_status,
            failure_reason=failure_reason,
            bundle_hashes={name: item.bundle_hash for name, item in stored_artifacts.items()},
            revision_hashes=revision_hashes,
            execution_id=execution_id,
            replay_verified=replay_verified,
            artifact_paths={name: str(item.path) for name, item in stored_artifacts.items()},
            restore_verified=False,
        )
    finally:
        PARSER_PATH.write_text(original_source, encoding="utf-8")
        restored_source = PARSER_PATH.read_text(encoding="utf-8")
        restore_verified = restored_source == original_source
        if not restore_verified:
            raise RuntimeError("Failed to restore src/parser.py to its baseline content.")

    if result is None:
        raise RuntimeError("Workflow did not produce a result.")

    result.restore_verified = restore_verified
    return result


def create_shadow_client() -> ShadowClient:
    client = ShadowClient()
    try:
        client.list_revisions(PACKAGE_ID, limit=1)
        return client
    except ShadowThreadsError as error:
        raise RuntimeError(
            f"Shadow Threads server not reachable at {client.base_url}\n"
            "Please start the backend service before running this workflow."
        ) from error


def capture_artifact(
    *,
    client: ShadowClient,
    name: str,
    schema: str,
    payload: dict[str, Any],
    references: list[ArtifactReference] | None = None,
) -> StoredArtifact:
    path = ARTIFACTS_DIR / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    result = client.capture_artifact(
        schema=schema,
        package_id=PACKAGE_ID,
        payload=payload,
        references=references or [],
    )
    return StoredArtifact(name=name, path=path, bundle_hash=result.bundle_hash)


def create_revision(
    *,
    client: ShadowClient,
    artifacts: list[ArtifactReference],
    message: str,
    source: str,
    timestamp: str,
    parent_revision_hash: str | None = None,
) -> str:
    result = client.create_revision(
        package_id=PACKAGE_ID,
        artifacts=artifacts,
        metadata=RevisionMetadata(
            author="Shadow Threads Demo",
            message=message,
            created_by="run_workflow.py",
            timestamp=timestamp,
            source=source,
            tags=["demo", "coding-workflow"],
        ),
        parent_revision_hash=parent_revision_hash,
    )
    return result.revision_hash


def build_test_report(test_run: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    combined_output = "\n".join(
        part for part in (test_run.stdout.strip(), test_run.stderr.strip()) if part
    )
    failing_test = extract_first_match(
        r"(?:ERROR|FAIL): ([^\s]+) \(",
        combined_output,
    )
    error_type = extract_first_match(
        r"\n([A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):",
        combined_output,
    )
    error_message = extract_first_match(
        r"\n[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception): (.+)",
        combined_output,
    )

    if test_run.returncode:
        summary = (
            "Whitespace-only token was mutated to an empty string in shared parser state, "
            "then parsed as an integer."
        )
    else:
        summary = "All parser tests passed."

    return {
        "status": "failure" if test_run.returncode else "success",
        "command": TEST_COMMAND_DISPLAY,
        "returncode": test_run.returncode,
        "failing_test": failing_test,
        "failure_input": "1, 2, , 4" if test_run.returncode else None,
        "error_type": error_type,
        "error_message": error_message,
        "summary": summary,
        "output_excerpt": first_lines(combined_output, limit=12),
    }


def format_revision_history(
    client: ShadowClient,
    revision_hashes: dict[str, str],
) -> list[str]:
    ordered_revisions = [
        ("R3", revision_hashes.get("R3")),
        ("R2", revision_hashes.get("R2")),
        ("R1", revision_hashes.get("R1")),
    ]
    lines = []
    for index, (label, revision_hash) in enumerate(ordered_revisions):
        if not revision_hash:
            continue
        revision = client.get_revision(revision_hash)
        prefix = "" if index == 0 else "   " * (index - 1) + "\u2514\u2500 "
        lines.append(f"{prefix}{label} {revision.message}")
    return lines


def timestamp_for(offset_seconds: int) -> str:
    return (BASE_TIME + timedelta(seconds=offset_seconds)).isoformat()


def hash_prompt(prompt: str) -> str:
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()


def extract_first_match(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text)
    if not match:
        return None
    return match.group(1).strip()


def first_lines(text: str, *, limit: int) -> list[str]:
    if not text:
        return []
    return text.splitlines()[:limit]
