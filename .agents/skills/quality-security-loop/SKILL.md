---
name: quality-security-loop
description: >
  Use when closing a Python coding task, choosing quality or security checks,
  or deciding whether the agent delivery loop still needs another pass on a
  data-platform change.
---

# Qualidade, segurança e loop de entrega

Fonte da verdade (não copie o texto dessas páginas; abra e siga):

- `docs/qualidade-seguranca.md` lista as ferramentas e o papel de cada uma.
- `docs/agent-delivery-loop.md` define quando cada check entra e como o loop fecha a tarefa.

## Quando aplicar

A decisão olha o diff, não o título da tarefa. O mapa está em `loop.yaml` e na tabela da página do loop:

- Python no diff: Ruff e mypy nos arquivos tocados.
- Código Python: Bandit.
- Qualquer mudança: gitleaks.
- Arquivo de dependência: pip-audit.
- Dockerfile, imagem, Terraform ou CloudFormation: Trivy.

Schemathesis não é um desses checks mecânicos. Se a tarefa muda a API HTTP, use a skill `schemathesis-api` e o spec OpenAPI. Contrato e regra de domínio continuam no pipeline.

## Como fechar a tarefa

1. Altere só o código da tarefa.
2. Rode `python3 scripts/agent_loop.py` (ou `apm run loop`, ou o prompt `run-agent-loop`). `apm run lint`, `apm run test` e `apm run audit` chamam `scripts/lint.sh`, `scripts/test.sh` e `scripts/audit.sh` com os mesmos argv de `loop.yaml`.
3. Se um check falhar, o feedback é só `propriedade_quebrada` e `contraexemplo_minimo`. Corrija isso. Não explique o próprio erro.
4. Se o hash da falha se repetir, descarte o patch e pare aquela linha.
5. Pare no limite de 3 voltas. Não suba o teto.
6. Só feche quando o que falhava passa e o que já passava continua passando.
7. Ferramenta ausente é falha. Não finja que passou.
8. Não desligue o check com `noqa`, `type: ignore` ou baseline, a menos que a tarefa peça isso.

Fonte extra: `docs/papers-research.md`. Ao fechar, relate checks rodados, volta em que passou e o comando. O CI continua sendo o gate de merge.
