#!/usr/bin/env python3
"""Mutantes explícitos do harness.

Aplica um mutante, roda a suíte, restaura, e relata morto/sobreviveu.
Não inventa pontuação: só o que esta corrida medir.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOMAIN = ROOT / "sample" / "domain.py"
LOOP = ROOT / "scripts" / "agent_loop.py"
SAMPLE_LOOP = ROOT / "sample" / "loop.yaml"
SUITE = [
    sys.executable,
    "-m",
    "unittest",
    "tests.test_agent_loop",
    "tests.test_agent_loop_integration",
    "-q",
]


def run_suite() -> int:
    return subprocess.run(SUITE, cwd=ROOT, check=False).returncode


def apply_and_test(label: str, path: Path, old: str, new: str) -> str:
    original = path.read_text(encoding="utf-8")
    if old not in original:
        return f"{label}: NAO_APLICADO (trecho ausente)"
    path.write_text(original.replace(old, new, 1), encoding="utf-8")
    try:
        code = run_suite()
    finally:
        path.write_text(original, encoding="utf-8")
    if code == 0:
        return f"{label}: SOBREVIVEU (suíte ficou verde)"
    return f"{label}: MORTO (suíte falhou, exit {code})"


def main() -> int:
    results = [
        apply_and_test(
            "domain: inserir comparação invertida (amount < 10000)",
            DOMAIN,
            "    if amount > daily_limit:\n"
            "        return TransferResult(status=\"REJEITADA\", origin_balance=origin_balance)\n"
            "    return TransferResult(\n"
            "        status=\"APROVADA\",\n"
            "        origin_balance=origin_balance - amount,\n"
            "    )\n",
            "    if amount > daily_limit:\n"
            "        return TransferResult(status=\"REJEITADA\", origin_balance=origin_balance)\n"
            "    if amount < 10000:\n"
            "        return TransferResult(status=\"PENDENTE_APROVACAO\", origin_balance=origin_balance)\n"
            "    return TransferResult(\n"
            "        status=\"APROVADA\",\n"
            "        origin_balance=origin_balance - amount,\n"
            "    )\n",
        ),
        apply_and_test(
            "loop.yaml: tirar o check pytest-domain",
            SAMPLE_LOOP,
            "  - name: pytest-domain\n",
            "  - name: pytest-skip\n",
        ),
        apply_and_test(
            "agent_loop: quebrar hash_failure",
            LOOP,
            "return hashlib.sha256(payload).hexdigest()",
            "return '0'",
        ),
    ]
    print("Mutantes explícitos")
    killed = 0
    survived = 0
    skipped = 0
    for line in results:
        print(line)
        if line.endswith("NAO_APLICADO (trecho ausente)") or "NAO_APLICADO" in line:
            skipped += 1
        elif "MORTO" in line:
            killed += 1
        elif "SOBREVIVEU" in line:
            survived += 1
    total = killed + survived
    score = (killed / total) if total else 0.0
    print(f"mortos={killed} sobreviveram={survived} nao_aplicados={skipped}")
    print(f"score={score:.2f} (mortos/aplicados)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
