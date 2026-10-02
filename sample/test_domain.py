"""Teste da regra nomeada: acima de 10000 fica pendente e o saldo não muda."""

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
