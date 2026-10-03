---
trigger: glob
globs:
  - "**/*openapi*.{yaml,yml,json}"
  - "**/*swagger*.{yaml,yml,json}"
  - "**/openapi.yaml"
  - "**/openapi.yml"
  - "**/openapi.json"
---

- Este arquivo é spec de contrato HTTP. A tarefa que o altera (ou a implementação que ele descreve) não fecha sem Schemathesis contra este spec.
- Schemathesis é o validador de API deste harness: gera casos a partir do OpenAPI e procura quebra inesperada com fuzzing property-based. Complementa a camada de contrato e a camada de regra de domínio já descritas no repositório.
- Comando do pacote: `apm run schemathesis --param spec=<este-arquivo-ou-url>`. Não existe chave `tools` no `apm.yml`; este script e esta instrução são o encaixe oficial.
- Fonte da verdade: `docs/schemathesis.md`. Não recrie a página aqui.
- O loop em `scripts/agent_loop.py` não substitui este passo.
