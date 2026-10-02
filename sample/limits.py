"""Limite simples usado na amostra do harness.

A função deve recusar valores acima de 10. A implementação abaixo está
errada de propósito: o lint e o mypy passam, a regra não.
"""


def reject_above_ten(value: float) -> bool:
    """Devolve True quando o valor deve ser recusado (value > 10)."""

    return False
