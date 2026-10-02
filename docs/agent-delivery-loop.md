# Loop de entrega do agente

Esta página continua a descoberta: desenvolvimento Python numa plataforma de dados na AWS. A tarefa de um agente de código só fecha quando as ferramentas de qualidade e segurança que se aplicam a ela passam. Se alguma reporta problema, o agente corrige e roda de novo. O CI continua sendo o gate de merge. O loop é o que impede o agente de declarar a tarefa pronta com falha conhecida.

Ferramentas, as mesmas de [qualidade e segurança](qualidade-seguranca.md): Ruff ou Flake8, mypy ou Pyright, Bandit, gitleaks ou TruffleHog, pip-audit ou Safety, Trivy.

A lista de papers e o que cada um contribui está em [Papers que informam o harness](papers-research.md). Abaixo só entra o que muda o desenho do loop.

## Arquitetura do loop

1. O agente altera o código da tarefa.
2. Um wrapper escolhe os checks desta mudança e executa.
3. O wrapper lê o resultado. Passou o que tinha de passar e o que já passava continua passando: a tarefa fecha, com a volta em que passou.
4. Falhou: o wrapper devolve só a propriedade quebrada e o menor contraexemplo. O agente corrige isso e volta ao passo 2.
5. O mesmo hash de falha se repete: o patch é descartado, a linha aborta.
6. Estourou o limite de 3 voltas: a tarefa não fecha.

O loop não substitui Schemathesis nem o cenário Gherkin. Contrato e regra de domínio continuam no pipeline. Este loop cobre o que as ferramentas mecânicas e o pytest da regra nomeada conseguem ver.

## O que roda em cada tarefa

| Mudança | Checks |
| --- | --- |
| Sempre que há Python | Ruff ou Flake8, e mypy ou Pyright |
| Diff em código Python | Bandit, e gitleaks ou TruffleHog |
| `requirements*.txt`, `pyproject.toml` ou lockfile | pip-audit ou Safety |
| Dockerfile, imagem, Terraform ou CloudFormation | Trivy |

A decisão olha o diff, não o título da tarefa. Sem arquivo Python novo, não roda mypy no repositório inteiro se o projeto ainda não está todo tipado: roda nos arquivos tocados. Sem mudança de dependência, não bloqueia a tarefa num advisory antigo que ninguém desta mudança introduziu. Segredo é a exceção: gitleaks ou TruffleHog roda em todo commit, porque um `.env` pode aparecer em qualquer tarefa.

## Guardrails (com a origem)

- **Máximo de 3 voltas.** Não subir o teto. Kiecker et al. 2026 (preprint) veem a maior parte do ganho nas primeiras 3 a 4 rodadas. Ao fechar, registre em qual tentativa passou.
- **Feedback mínimo.** A falha que volta ao agente é a propriedade quebrada e o menor contraexemplo, não o log inteiro da ferramenta. Não peça ao modelo para explicar o próprio erro (He et al., preprint; Olausson et al. 2024, ICLR, no gargalo da qualidade do feedback).
- **Hash da falha.** Hasheie ferramenta + mensagem normalizada + check. Se o hash se repetir, descarte o patch e aborte aquela linha. Reverta o patch que falhou antes da próxima tentativa (Bouzenia, Devanbu, Pradel 2024, RepairAgent, preprint).
- **Fechar só no fail-to-pass e pass-to-pass.** Os checks que tinham de começar a passar passam, e os que já passavam ainda passam (Jimenez et al. 2024, SWE-bench, ICLR).
- **Suíte fina não fecha.** Liu et al. 2023 (preprint) mostram que mais testes baixam o pass@k e podem mudar ranking. Este repo não roda EvalPlus. O extra da descoberta é o Schemathesis no OpenAPI e o pytest da regra nomeada.
- **Verde fino não basta.** Wang, Pradel e Liu 2025 (preprint) reportam inflação de 6,4 pontos percentuais absolutos na taxa de resolução quando a suíte é fraca. Não feche no primeiro verde estreito.
- **Regra nomeada fora do OpenAPI.** Maaz et al. 2025 (workshop NeurIPS) permitem inferir uma propriedade do cenário pytest-bdd, gerar um teste de propriedade e só gastar volta de correção se uma segunda leitura confirmar bug real. Isso não substitui o Schemathesis.
- **Input vizinho.** Honarvar, van der Wilk e Donaldson 2025 (IEEE ICST): só o abstract foi lido. Antes de fechar, rode a mesma propriedade num input próximo. Um único exemplo verde não basta.
- **Não desligar o check.** O agente não comenta `# noqa`, não adiciona `# type: ignore` e não põe o achado no baseline, a menos que a tarefa peça isso.

## Como implementar

Três encaixes, no mesmo cenário Python na AWS. O agente chama um deles. O CI repete o mesmo comando, para o que fugiu do loop local.

**Wrapper.** `scripts/agent_loop.py` lê `loop.yaml` (ou `sample/loop.yaml` na amostra), escolhe os checks pelo glob, hasheia a falha, devolve feedback mínimo e só fecha no fail-to-pass com pass-to-pass. Como rodar: [Amostra do loop](agent-loop-sample.md).

**pre-commit.** O mesmo conjunto em `.pre-commit-config.yaml`. O hook dispara no commit. Serve para humano e para agente que commita. Não vê Trivy de imagem que só existe no build. Por isso o CI repete.

**CI.** GitHub Actions ou AWS CodeBuild roda o wrapper de novo no pull request. Falha bloqueia o merge, igual à página de qualidade. O loop do agente é a primeira passagem. O CI é a que vale.

O que ainda falta para produção está em [Checklist de produção](production-checklist.md).
