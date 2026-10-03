#!/usr/bin/env python3
"""Oráculo do limiar da amostra, sem corrigir o bug intencional.

O mutante `amount < 10000` sobreviveu porque a suíte só exercitava
valores acima de 10000. Nesses inputs a comparação invertida é falsa e
o código cai no mesmo APROVADA do bug (aprovar e debitar). O caso
9999.99 separa os dois: o bug intencional aprova; o mutante deixa
pendente.
"""

from __future__ import annotations

import unittest

from sample.domain import approve_transfer


class DomainThresholdOracleTests(unittest.TestCase):
    def test_amount_below_10000_is_approved_and_debited_on_intentional_bug(self) -> None:
        origin = 50000.0
        amount = 9999.99
        result = approve_transfer(
            amount=amount,
            daily_limit=100000.0,
            origin_balance=origin,
        )
        self.assertEqual(result.status, "APROVADA")
        self.assertEqual(result.origin_balance, origin - amount)

    def test_amount_equal_to_10000_is_approved_and_debited(self) -> None:
        origin = 50000.0
        amount = 10000.0
        result = approve_transfer(
            amount=amount,
            daily_limit=100000.0,
            origin_balance=origin,
        )
        self.assertEqual(result.status, "APROVADA")
        self.assertEqual(result.origin_balance, origin - amount)
