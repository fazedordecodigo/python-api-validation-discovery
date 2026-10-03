---
name: schemathesis-api
description: >
  Use when the task changes an HTTP API, an OpenAPI spec, or routes covered
  by contract tests. Run Schemathesis against the spec before calling the
  task done.
---

# Schemathesis no contrato HTTP

Fonte da verdade: `docs/schemathesis.md`. Não copie essa página. Ela explica por que o Schemathesis é a camada de contrato desta descoberta: gera casos a partir do OpenAPI (property-based / fuzzing) e procura quebra inesperada.

## O que isto complementa

- Camada de contrato: Schemathesis no spec OpenAPI.
- Camada de regra de domínio: Gherkin (pytest-bdd ou Behave), descrita em `docs/regras-de-negocio.md`.
- Checks mecânicos (lint, tipo, SAST, segredo, dependência, imagem): `docs/qualidade-seguranca.md` e o wrapper `scripts/agent_loop.py`.

Uma tarefa que muda a API não está pronta só com o loop de lint. O contrato precisa aguentar o que o spec permite.

## Como rodar

O `apm.yml` não tem chave `tools`. O Schemathesis entra como script nomeado e como esta skill:

```bash
apm run schemathesis --param spec=<caminho-ou-url-do-openapi>
```

Equivalente direto:

```bash
python3 -m schemathesis run <caminho-ou-url-do-openapi>
```

Aponte para o spec da API da plataforma de dados. Falha dura se a implementação divergir do contrato. Não invente um spec na hora para mascarar a divergência.

Se a tarefa só muda Python sem tocar contrato HTTP, esta skill não bloqueia o encerramento. Se muda rota, schema, status ou o próprio OpenAPI, rode o Schemathesis antes de fechar.
