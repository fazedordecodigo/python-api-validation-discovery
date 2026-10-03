---
description: Uma tarefa de código só fecha quando os checks aplicáveis passam.
applyTo: "**/*"
---

- Uma tarefa de código não está pronta enquanto os checks aplicáveis ao diff não passarem e os que já passavam continuarem passando.
- Escolha os checks pela mudança, como em `docs/agent-delivery-loop.md` e `loop.yaml`. Python no diff pede Ruff e mypy. Código Python pede Bandit. Qualquer mudança pede gitleaks. Arquivo de dependência pede pip-audit. Dockerfile, imagem, Terraform ou CloudFormation pedem Trivy.
- Rode `python3 scripts/agent_loop.py` ou `apm run loop` antes de encerrar. O feedback é a propriedade quebrada e o menor contraexemplo, não o log cru. Os scripts `apm run lint`, `apm run test` e `apm run audit` expõem o mesmo conjunto sem mudar a lógica dos checks.
- Hash repetido descarta o patch e aborta a linha. O teto é 3 voltas.
- Ferramenta ausente é falha. Não trate ausência como sucesso.
- Não desligue o check com `noqa`, `type: ignore` ou baseline, a menos que a tarefa peça isso.
- Se a tarefa muda a API HTTP ou o spec OpenAPI, os checks mecânicos não bastam: rode Schemathesis contra o spec (`apm run schemathesis --param spec=<openapi>`). Fonte: `docs/schemathesis.md`.
- O CI continua sendo o gate de merge. O loop local é a primeira passagem.
