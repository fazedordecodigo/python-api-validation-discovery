"""Teste da regra nomeada: acima de 10000 fica pendente e o saldo não muda.

O lado de baixo do limiar (amount <= 10000) também é oráculo: sem ele,
`amount < 10000` e o bug intencional (sempre aprova) produzem o mesmo
resultado para 10000.01.
"""

import pytest

from sample.domain import approve_transfer


@pytest.mark.parametrize("amount", [10000.01, 10000.02])
def test_amount_above_10000_is_pending_and_balance_unchanged(amount: float) -> None:
    origin = 50000.0
    result = approve_transfer(
        amount=amount,
        daily_limit=100000.0,
        origin_balance=origin,
    )
    assert result.status == "PENDENTE_APROVACAO", (
        "propriedade: amount > 10000 implica PENDENTE_APROVACAO e saldo intacto; "
        f"contraexemplo: {amount}"
    )
    assert result.origin_balance == origin, (
        "propriedade: amount > 10000 não debita o saldo de origem; "
        f"contraexemplo: {amount}"
    )


@pytest.mark.parametrize("amount", [9999.99, 10000.0])
def test_amount_at_or_below_10000_is_approved_and_debited(amount: float) -> None:
    origin = 50000.0
    result = approve_transfer(
        amount=amount,
        daily_limit=100000.0,
        origin_balance=origin,
    )
    assert result.status == "APROVADA", (
        "propriedade: amount <= 10000 é aprovado e o saldo é debitado; "
        f"contraexemplo: {amount}"
    )
    assert result.origin_balance == origin - amount, (
        "propriedade: amount <= 10000 debita o saldo de origem; "
        f"contraexemplo: {amount}"
    )
