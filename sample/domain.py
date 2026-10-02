"""Regra nomeada da amostra: valor acima de 10000 fica pendente.

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
    não é debitado. A implementação abaixo ignora essa regra de propósito.
    Ruff e mypy não veem o defeito.
    """

    if amount > daily_limit:
        return TransferResult(status="REJEITADA", origin_balance=origin_balance)
    return TransferResult(
        status="APROVADA",
        origin_balance=origin_balance - amount,
    )
