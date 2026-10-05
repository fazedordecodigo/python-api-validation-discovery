# Plano de execução da verificação

O `loop.yaml` da raiz fecha sem os testes que pegam os bugs da amostra. Siga os passos na ordem. Cada passo termina num comando e num resultado visível.

Não corrija `sample/domain.py` nem `sample/limits.py`. O bug prova que o fechamento vê a regra. `approve_transfer` aprova acima de 10000. `reject_above_ten` devolve sempre `False`.

O desenho do loop já está em [Loop de entrega do agente](agent-delivery-loop.md). Os papers que o desenharam estão em [Papers que informam o harness](papers-research.md). Este plano só muda o que o fechamento executa.

## Rode o pytest da regra no loop da raiz

`sample/loop.yaml` já chama `pytest sample/test_domain.py sample/test_limits.py`. O `loop.yaml` da raiz não chama.

1. Copie o tool `pytest-domain` para o `loop.yaml` da raiz.
2. Mantenha `pass_files: false` e `apply: python`.
3. Atualize `test_root_loop_yaml_maps_quality_tools` para esperar o tool novo.
4. Atualize `test_python_change_selects_lint_types_sast_and_secrets` para esperar `pytest-domain`.

Qualquer diff com `.py` passa a rodar os dois arquivos. O predicado é o mesmo da amostra.

Confira com o bug ainda no código.

```bash
python3 scripts/agent_loop.py --changed-files sample/domain.py
```

O processo sai com código 1. A saída contém `propriedade_quebrada`. A saída não contém `Traceback`.

## Faça o script de mutantes sair com erro

`scripts/run_explicit_mutants.py` imprime `SOBREVIVEU` e retorna 0. A suíte é `tests.test_agent_loop`, `tests.test_agent_loop_integration` e `tests.test_sample_domain_oracle`.

1. Retorne 1 quando `sobreviveram` for maior que zero.
2. Deixe a suíte como está.

Não acrescente `sample/test_domain.py` neste passo. Esse arquivo já falha no código atual. Um mutante pareceria morto pelo vermelho antigo.

Confira os três mutantes atuais.

```bash
python3 scripts/run_explicit_mutants.py
```

Os três saem `MORTO` e o processo sai 0.

Para ver o código 1, troque um trecho que a suíte não cobre. Rode o script. Leia `SOBREVIVEU` e exit 1. Restaure o arquivo antes de seguir.

O mutante `amount < 10000` morre no teste de 9999.99. Esse teste também passa no bug intencional. Ele não substitui o pytest de `PENDENTE_APROVACAO`.

O mutante que renomeia `pytest-domain` morre porque `test_sample_loop_yaml_selects_ruff_mypy_pytest` exige o nome. Não use esse mutante como prova da regra de transferência.

## Dispare o Schemathesis quando o diff tiver OpenAPI

Não há spec OpenAPI neste repositório. O alias `apm run schemathesis` não entra em `run_loop`.

1. Acrescente um `ApplyKind` para OpenAPI. `tool_applies` rejeita valor fora da enum. O teste `test_rejects_unknown_apply` cobre essa recusa.
2. Trate o kind como `dependencies`. O tool roda só quando um path casa com o padrão.
3. Ponha o tool no `loop.yaml` da raiz. O argv é `python3 -m schemathesis run`. Com `pass_files: true`, o spec mudado entra no comando.
4. Copie os padrões de OpenAPI e Swagger já listados em `AGENTS.md`.
5. Se mais de um spec mudar, rode uma vez por arquivo.
6. Estenda os testes de seleção. Um path `openapi.yaml` seleciona o tool. Um `.py` não seleciona.

Não aponte o teste de unidade para um servidor. Injete `which` e `run`, como os testes de ferramenta ausente.

Um diff só de Python não espera o Schemathesis. O job contra o stage do API Gateway continua o de [CI na AWS](aws-ci.md). O diff local não vê o stage.

## Repita o comando no CI

Não há workflow nem `.pre-commit-config.yaml`.

1. Adicione um workflow do GitHub Actions que rode `python3 scripts/agent_loop.py` no pull request.
2. Instale as ferramentas do `loop.yaml` no job. Ferramenta ausente já faz o loop sair 1.
3. Se a plataforma usar CodeBuild, chame o mesmo comando. Não crie um segundo mapa de tools.

O [Checklist de produção](production-checklist.md) marca como abertos o teto de 3 voltas, o hash, o feedback mínimo e o fail-to-pass. `scripts/agent_loop.py` já faz isso. Marque esses itens ao atualizar a página. Deixe abertos pre-commit, Schemathesis noturno e pytest-bdd no PR até existirem neste repositório.

pytest-bdd continua sem arquivo `.feature`. O pytest da amostra é o substituto desta leva. Não escreva o Gherkin HTTP aqui.

## Não faça nesta leva

- Não ponha um mínimo de cobertura. Hamidi e outros mediram cobertura e mutação em código gerado por modelo, e a detecção dos defeitos difíceis ficou perto de zero quando a asserção não via o defeito. O texto está em [arXiv 2609.09315](https://arxiv.org/abs/2609.09315).
- Não peça ao agente para escrever a suíte. Chen e outros viram que mudar o volume de testes escritos na trajetória não muda o desfecho. O texto está em [arXiv 2602.07900](https://arxiv.org/abs/2602.07900).
- Não acrescente uma segunda leitura por outro modelo. Hu e outros viram retorno menor de harness mais pesado em reparo do tipo SWE. O texto está em [arXiv 2609.32459](https://arxiv.org/abs/2609.32459).
- Não troque os valores 9999.99, 10000.0, 10000.01 e 10000.02 por Hypothesis. Só escreva uma estratégia se um mutante sobreviver a esses quatro. PBT-Bench mostra que a estratégia importa e que o andaime pode piorar um modelo forte. O texto está em [arXiv 2605.15229](https://arxiv.org/abs/2605.15229).
- Não suba `max_iterations` acima de 3. O YAML e `--max-iterations` aceitam um número maior. Não imponha a trava nesta leva.
- Não mude o momento da restauração. Hash repetido e teto restauram o snapshot do início. Entre tentativas o patch fica. Crash do agente restaura só o snapshot de antes daquela chamada.
- Não troque o gitleaks para histórico, o pip-audit para um path, nem o Trivy para imagem. gitleaks varre a árvore com `--no-git --source .`. pip-audit roda sem o arquivo que disparou o tool. O argv do Trivy é `trivy fs`.

## Ordem

Faça o pytest da raiz primeiro e confira o exit 1. Depois mude o exit do script de mutantes. Depois a seleção do Schemathesis. O CI fica por último. O job deve falhar no mesmo bug que o loop local já falha.
