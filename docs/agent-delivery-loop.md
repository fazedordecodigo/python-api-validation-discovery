# Loop de entrega do agente

Esta página continua a descoberta: desenvolvimento Python numa plataforma de dados na AWS. A tarefa de um agente de código só fecha quando as ferramentas de qualidade e segurança que se aplicam a ela passam. Se alguma reporta problema, o agente corrige e roda de novo. O CI continua sendo o gate de merge. O loop é o que impede o agente de declarar a tarefa pronta com falha conhecida.

Ferramentas, as mesmas de [qualidade e segurança](qualidade-seguranca.md): Ruff ou Flake8, mypy ou Pyright, Bandit, gitleaks ou TruffleHog, pip-audit ou Safety, Trivy.

## Arquitetura do loop

1. O agente altera o código da tarefa.
2. Um wrapper (script ou hook) escolhe os checks desta mudança e executa.
3. O agente lê a saída. Passou tudo: a tarefa fecha, com o resumo do que rodou.
4. Falhou: o agente trata a saída como o próximo defeito, corrige só isso, e volta ao passo 2.
5. Estourou o limite de voltas: a tarefa não fecha. O agente devolve a falha e para.

O loop não substitui Schemathesis nem o cenário Gherkin. Contrato e regra de negócio continuam no pipeline. Este loop cobre o que as ferramentas mecânicas conseguem ver.

## O que roda em cada tarefa

| Mudança | Checks |
| --- | --- |
| Sempre que há Python | Ruff ou Flake8, e mypy ou Pyright |
| Diff em código Python | Bandit, e gitleaks ou TruffleHog |
| `requirements*.txt`, `pyproject.toml` ou lockfile | pip-audit ou Safety |
| Dockerfile, imagem, Terraform ou CloudFormation | Trivy |

A decisão olha o diff, não o título da tarefa. Sem arquivo Python novo, não roda mypy no repositório inteiro se o projeto ainda não está todo tipado: roda nos arquivos tocados. Sem mudança de dependência, não bloqueia a tarefa num advisory antigo que ninguém desta mudança introduziu. Segredo é a exceção: gitleaks ou TruffleHog roda em todo commit, porque um `.env` pode aparecer em qualquer tarefa.

## Como implementar

Três encaixes, no mesmo cenário Python na AWS. O agente chama um deles. O CI repete o mesmo comando, para o que fugiu do loop local.

**Wrapper.** Um script `scripts/agent-check.sh` que o agente é obrigado a chamar antes de encerrar. Ele vê o diff contra a base, monta a lista da tabela e sai com código diferente de zero se algo falhou. A saída fica em texto, para o agente ler.

**pre-commit.** O mesmo conjunto em `.pre-commit-config.yaml`. O hook dispara no commit. Serve para humano e para agente que commita. Não vê Trivy de imagem que só existe no build. Por isso o CI repete.

**CI.** GitHub Actions ou AWS CodeBuild roda o wrapper de novo no pull request. Falha bloqueia o merge, igual à página de qualidade. O loop do agente é a primeira passagem. O CI é a que vale.

## Guardrails

- **Máximo de voltas.** Três correções para o mesmo check. Na quarta falha igual, para. Sem isso o agente reescreve o arquivo para sempre.
- **Mesma falha.** Se a assinatura do erro (ferramenta + arquivo + código) não mudou, conta como volta gasta. Erro novo reinicia a contagem daquele item, não da tarefa inteira.
- **Não desligar o check.** O agente não comenta `# noqa`, não adiciona `# type: ignore` e não põe o achado no baseline para a tarefa passar, a menos que a tarefa peça isso.
- **Relato.** Ao fechar, o agente devolve: checks rodados, volta em que passou, e comando. Ao parar, devolve a última saída e o motivo (limite ou check que não soube corrigir). O pull request não nasce "pronto" sem esse relato.
