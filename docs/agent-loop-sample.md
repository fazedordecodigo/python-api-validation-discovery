# Amostra do loop de entrega

Esta página mostra o protótipo do loop descrito em [Loop de entrega do agente](agent-delivery-loop.md). Continua a mesma descoberta: desenvolvimento Python numa plataforma de dados na AWS.

O wrapper `scripts/agent_loop.py` lê um YAML de checks, escolhe ferramentas pelo glob do diff e executa. Se algum falha, o texto que volta ao agente é só a propriedade quebrada e o menor contraexemplo. O mesmo hash de falha descarta o patch e aborta a linha. O loop só fecha quando o check que falhava passa e os que já passavam continuam passando. O teto é 3 voltas. Ferramenta ausente é falha explícita.

Há dois mapas:

- `loop.yaml` na raiz: Ruff, mypy, Bandit, gitleaks, pip-audit e Trivy, alinhados à tabela da página do loop.
- `sample/loop.yaml`: Ruff, mypy e o pytest da regra nomeada, para a corrida ponta a ponta.

Schemathesis não entra no wrapper. Contrato HTTP continua no pipeline. Veja [Schemathesis](schemathesis.md) e [Pacote APM](apm-setup.md).

## Amostra de domínio (`sample/`)

`sample/domain.py` tem um defeito que Ruff e mypy não veem: `approve_transfer` deveria deixar pendente um valor acima de 10000 e não debitar o saldo de origem, mas aprova e debita. É o mesmo exemplo de [regras de negócio](regras-de-negocio.md), em Python puro. `sample/limits.py` tem uma regra menor (recusar valor acima de 10), também errada de propósito.

O pytest em `sample/test_domain.py` fixa a regra: 10000.01 e o vizinho 10000.02 devem voltar `PENDENTE_APROVACAO` com saldo intacto.

## Como rodar a amostra

Na raiz do repositório, com Ruff, mypy e pytest no `PATH`:

```bash
python3 scripts/agent_loop.py \
  --config sample/loop.yaml \
  --changed-files sample/domain.py sample/limits.py \
  --agent "python3 sample/mock_agent.py"
```

`sample/mock_agent.py` lê `propriedade_quebrada` e `contraexemplo_minimo` e só então reescreve o arquivo. Não é um agente de código real.

O log de uma corrida executada neste repositório está em `sample/run.log`. A evidência dos testes do harness (16 unittest OK; mutantes mortos=2, sobreviveram=1, score=0.67) está em `docs/test-run.md`.

`--demo` ainda existe e usa `scripts/demo_agent.py` num fixture temporário, sem chamar um agente real.

## Sem agente, só o diff

```bash
python3 scripts/agent_loop.py --config sample/loop.yaml --changed-files sample/domain.py
```

A saída dos checks (já no formato mínimo) vai para stdin do comando, para `AGENT_LOOP_FEEDBACK_FILE` e para o placeholder `{feedback}` se você usar `--agent "meu-agente {feedback}"`.

## Testes do wrapper

```bash
python3 -m unittest tests.test_agent_loop tests.test_agent_loop_integration
```
