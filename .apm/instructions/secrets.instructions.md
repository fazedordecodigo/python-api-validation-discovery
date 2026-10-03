---
description: Varredura de segredo em qualquer mudança; um .env pode aparecer em qualquer tarefa.
applyTo: "**/*"
---

- Qualquer mudança pede gitleaks, com os mesmos argv de `loop.yaml`: `gitleaks detect --no-git --redact --no-banner --source .`.
- Segredo nunca fica no repositório, só em variável de ambiente.
- Fonte da verdade: `docs/qualidade-seguranca.md` e `loop.yaml`. Não recrie a página aqui.
- Ferramenta ausente é falha. Não trate ausência como sucesso.
- Auditoria nomeada: `apm run audit` ou `sh scripts/audit.sh`. O wrapper `python3 scripts/agent_loop.py` também roda gitleaks em todo diff.
