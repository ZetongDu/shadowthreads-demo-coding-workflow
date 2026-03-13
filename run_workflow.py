from __future__ import annotations

import sys

from src.workflow_engine import run_workflow


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    try:
        run_workflow()
    except Exception as error:
        print(str(error))
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
