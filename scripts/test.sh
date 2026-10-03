#!/bin/sh
# Suíte do harness. Não altera os testes; só os executa.
set -eu

python3 -m unittest \
  tests.test_agent_loop \
  tests.test_agent_loop_integration \
  tests.test_sample_domain_oracle
