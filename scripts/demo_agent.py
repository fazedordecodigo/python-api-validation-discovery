#!/usr/bin/env python3
"""Agente substituto para demonstrar o loop sem um agente de código real.

Lê a saída dos checks (arquivo em AGENT_LOOP_FEEDBACK_FILE ou stdin) e
aplica um conserto determinístico no fixture de exemplo.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

WORKDIR_ENV = "AGENT_LOOP_WORKDIR"
FEEDBACK_ENV = "AGENT_LOOP_FEEDBACK_FILE"
SAMPLE_RELATIVE = Path("examples/loop-demo/work/sample.py")
CLEAN_SOURCE = 'def greet(name: str) -> str:\n    return f"hello {name}"\n'


def read_feedback() -> str:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).read_text(encoding="utf-8")
    feedback_path = os.environ.get(FEEDBACK_ENV)
    if feedback_path and Path(feedback_path).is_file():
        return Path(feedback_path).read_text(encoding="utf-8")
    if sys.stdin.isatty():
        return ""
    return sys.stdin.read()


def resolve_sample() -> Path:
    workdir = Path(os.environ.get(WORKDIR_ENV, Path(__file__).resolve().parent.parent))
    return workdir / SAMPLE_RELATIVE


def main() -> int:
    feedback = read_feedback()
    sample = resolve_sample()
    if not sample.is_file():
        print(f"demo_agent: fixture não encontrado: {sample}", file=sys.stderr)
        return 1
    if (
        "ruff" in feedback
        or "F401" in feedback
        or "import morto" in feedback
        or "json" in sample.read_text(encoding="utf-8")
    ):
        sample.write_text(CLEAN_SOURCE, encoding="utf-8")
        print(f"demo_agent: reescreveu {sample} sem o import morto.")
        return 0
    print("demo_agent: nada para corrigir no fixture.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
