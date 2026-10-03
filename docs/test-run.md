# Corrida dos testes do harness

Comando e saída reais desta cópia de trabalho. PATH com `$HOME/.local/bin` (ruff, mypy, pytest).

## unittest (unitário + integração + oráculo do limiar)

```
$ python3 -m unittest tests.test_sample_domain_oracle tests.test_agent_loop tests.test_agent_loop_integration -v
test_amount_below_10000_is_approved_and_debited_on_intentional_bug ... ok
test_amount_equal_to_10000_is_approved_and_debited ... ok
test_extract_failure_prefers_labeled_property_and_example ... ok
test_format_feedback_is_property_plus_counterexample ... ok
test_hash_uses_tool_normalized_message_and_check ... ok
test_root_loop_yaml_maps_quality_tools ... ok
test_sample_loop_yaml_selects_ruff_mypy_pytest ... ok
test_close_requires_fail_to_pass_and_pass_to_pass ... ok
test_max_iterations_aborts_at_three ... ok
test_missing_tool_fails_clearly ... ok
test_rejects_unknown_apply ... ok
test_repeated_hash_discards_patch_and_aborts_line ... ok
test_run_check_command_and_count_iterations_until_pass ... ok
test_dependency_change_selects_audit_and_secrets ... ok
test_dockerfile_selects_trivy_and_secrets ... ok
test_python_change_selects_lint_types_sast_and_secrets ... ok
test_repeated_hash_aborts_when_agent_does_not_fix ... ok
test_ruff_mypy_clean_domain_pytest_fails_then_mock_fixes ... ok

Ran 18 tests in 2.145s
OK
unittest_exit=0
```

## mutmut

`pip install mutmut` instalou mutmut 3.8.0. O CLI exige `source_paths` e não foi a fonte desta pontuação.

## mutantes explícitos

Os mesmos três mutantes de antes, restaurados depois de cada corrida. `sample/domain.py` continua com o bug intencional (não há `if amount > 10000`).

```
$ python3 scripts/run_explicit_mutants.py
domain: inserir comparação invertida (amount < 10000): MORTO (suíte falhou, exit 1)
loop.yaml: tirar o check pytest-domain: MORTO (suíte falhou, exit 1)
agent_loop: quebrar hash_failure: MORTO (suíte falhou, exit 1)
mortos=3 sobreviveram=0 nao_aplicados=0
score=1.00 (mortos/aplicados)
mutants_exit=0
```

O mutante invertido morreu em `test_amount_below_10000_is_approved_and_debited_on_intentional_bug`: com `amount < 10000`, 9999.99 volta `PENDENTE_APROVACAO` em vez de `APROVADA`.
