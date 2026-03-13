"""Deterministic simulated AI refactor for the workflow demo."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import unified_diff


SIMULATED_PROMPT = (
    "Refactor parse_numbers so it strips whitespace before parsing each token."
)

BASELINE_SOURCE = '''"""Baseline parser used by the workflow demo."""


def parse_numbers(text):
    numbers = []
    for token in text.split(","):
        normalized = token.strip()
        if not normalized:
            continue
        numbers.append(int(normalized))
    return numbers
'''

REFACTORED_SOURCE = '''"""Baseline parser used by the workflow demo."""


def _normalize_tokens_in_place(tokens):
    for index, token in enumerate(tokens):
        tokens[index] = token.strip()
        if token == "":
            tokens.pop(index)
    return tokens


def parse_numbers(text):
    tokens = text.split(",")
    normalized_tokens = _normalize_tokens_in_place(tokens)
    return [int(token.strip()) for token in normalized_tokens]
'''


@dataclass(frozen=True)
class RefactorResult:
    plan: dict[str, str]
    refactored_source: str
    diff_text: str
    patch_payload: dict[str, str]


def generate_refactor_plan(source_code: str) -> dict[str, str]:
    if normalize_source(source_code) != normalize_source(BASELINE_SOURCE):
        raise ValueError("Unexpected baseline parser source.")

    return {
        "change": "strip whitespace",
        "target": "parser.py",
        "prompt": SIMULATED_PROMPT,
    }


def apply_refactor(source_code: str, plan: dict[str, str]) -> RefactorResult:
    if normalize_source(source_code) != normalize_source(BASELINE_SOURCE):
        raise ValueError("Refactor engine only supports the demo baseline source.")

    if plan.get("change") != "strip whitespace":
        raise ValueError("Unsupported refactor plan.")

    diff_text = "".join(
        unified_diff(
            source_code.splitlines(keepends=True),
            REFACTORED_SOURCE.splitlines(keepends=True),
            fromfile="src/parser.py",
            tofile="src/parser.py",
        )
    )

    return RefactorResult(
        plan=plan,
        refactored_source=REFACTORED_SOURCE,
        diff_text=diff_text,
        patch_payload={
            "type": "code_patch",
            "change": plan["change"],
            "target": plan["target"],
            "diff": diff_text,
        },
    )


def normalize_source(source_code: str) -> str:
    return source_code.rstrip() + "\n"
