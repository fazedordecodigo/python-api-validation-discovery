# Corrida dos testes do harness

Comando e saída reais desta cópia de trabalho. PATH com `$HOME/.local/bin` (ruff 0.16.10, mypy 2.4.0, pytest 9.1.1).

## unittest (unitário + integração)

```
$ python3 -m unittest tests.test_agent_loop tests.test_agent_loop_integration -v
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

Ran 16 tests in 1.852s
OK
unittest_exit=0
```

## mutmut

`pip install mutmut` instalou mutmut 3.8.0. `mutmut --version` falhou: o CLI exige `source_paths` no setup.cfg e não foi a fonte desta pontuação.

## mutantes explícitos

```
$ python3 scripts/run_explicit_mutants.py
Mutantes explícitos
domain: inserir comparação invertida (amount < 10000): SOBREVIVEU (suíte ficou verde)
loop.yaml: tirar o check pytest-domain: MORTO (suíte falhou, exit 1)
agent_loop: quebrar hash_failure: MORTO (suíte falhou, exit 1)
mortos=2 sobreviveram=1 nao_aplicados=0
score=0.67 (mortos/aplicados)
mutants_exit=0
```

Lacuna: o mutante que coloca `amount < 10000` em `sample/domain.py` sobreviveu. A suíte continua verde porque o mock ainda conserta a partir do feedback e os testes unitários não assertam o operador da regra.
