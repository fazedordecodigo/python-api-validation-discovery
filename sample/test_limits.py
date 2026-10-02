"""Teste da regra simples: recusar valor acima de 10."""

from sample.limits import reject_above_ten


def test_value_above_ten_is_rejected() -> None:
    value = 10.01
    accepted = reject_above_ten(value)
    assert accepted is True, (
        "propriedade: value > 10 deve ser recusado; "
        "contraexemplo: 10.01"
    )
