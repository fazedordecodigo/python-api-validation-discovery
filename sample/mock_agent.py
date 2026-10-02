#!/usr/bin/env python3
"""Agente substituto da amostra. Lê o feedback mínimo e aplica um conserto.

Não é um agente de código real. Só entende as duas regras desta amostra.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

WORKDIR_ENV = "AGENT_LOOP_WORKDIR"
FEEDBACK_ENV = "AGENT_LOOP_FEEDBACK_FILE"

DOMAIN_FIX = '''"""Regra nomeada da amostra: valor acima de 10000 fica pendente.

O mesmo exemplo de domínio de docs/regras-de-negocio.md, em Python puro
para o harness local. Não substitui o cenário Gherkin no pipeline.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TransferResult:
    status: str
    origin_balance: float


def approve_transfer(
    amount: float,
    daily_limit: float,
    origin_balance: float = 50000.0,
) -> TransferResult:
    """Aprova, rejeita ou deixa pendente uma transferência da plataforma.

    Regra: amount > 10000 implica PENDENTE_APROVACAO e o saldo de origem
    não é debitado.
    """

    if amount > daily_limit:
        return TransferResult(status="REJEITADA", origin_balance=origin_balance)
    if amount > 10000:
        return TransferResult(status="PENDENTE_APROVACAO", origin_balance=origin_balance)
    return TransferResult(
        status="APROVADA",
        origin_balance=origin_balance - amount,
    )
'''

LIMITS_FIX = '''"""Limite simples usado na amostra do harness."""


def reject_above_ten(value: float) -> bool:
    """Devolve True quando o valor deve ser recusado (value > 10)."""

    return value > 10
'''


def read_feedback() -> str:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).read_text(encoding="utf-8")
    feedback_path = os.environ.get(FEEDBACK_ENV)
    if feedback_path and Path(feedback_path).is_file():
        return Path(feedback_path).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def parse_feedback(text: str) -> tuple[str, str]:
    property_broken = ""
    example = ""
    for line in text.splitlines():
        lowered = line.lower()
        if lowered.startswith("propriedade_quebrada:"):
            property_broken = line.split(":", 1)[1].strip()
        elif lowered.startswith("contraexemplo_minimo:"):
            example = line.split(":", 1)[1].strip()
    return property_broken, example


def main() -> int:
    workdir = Path(os.environ.get(WORKDIR_ENV, Path(__file__).resolve().parent.parent))
    feedback = read_feedback()
    property_broken, example = parse_feedback(feedback)
    if not property_broken and not example:
        print("mock_agent: feedback sem propriedade_quebrada/contraexemplo_minimo", file=sys.stderr)
        return 1
    blob = f"{property_broken} {example}".lower()
    wrote = False
    if "10000" in blob or "pendente" in blob:
        target = workdir / "sample" / "domain.py"
        target.write_text(DOMAIN_FIX, encoding="utf-8")
        print(f"mock_agent: leu o feedback e reescreveu {target}")
        wrote = True
    if "10.01" in blob or "value > 10" in blob or "acima de 10" in blob:
        target = workdir / "sample" / "limits.py"
        target.write_text(LIMITS_FIX, encoding="utf-8")
        print(f"mock_agent: leu o feedback e reescreveu {target}")
        wrote = True
    if not wrote:
        print(
            "mock_agent: leu o feedback e não soube mapear um conserto",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
