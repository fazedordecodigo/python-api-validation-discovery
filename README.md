# Pacote APM: qualidade e segurança

Este repositório é um pacote do [Agent Package Manager](https://microsoft.github.io/apm/) com as validações de qualidade e segurança já documentadas aqui (Ruff, mypy, Bandit, gitleaks, pip-audit, Trivy), o loop de entrega do agente e o Schemathesis no contrato OpenAPI.

Alvos do manifesto: `windsurf` (Devin Desktop) e `claude`. O APM não tem slug `devin`.

## Instalar o CLI

```bash
curl -sSL https://aka.ms/apm-unix | sh
```

## Instalar este pacote noutro repositório

```bash
apm install fazedordecodigo/python-api-validation-discovery
```

Com caminho local (útil num piloto):

```bash
apm install /caminho/para/python-api-validation-discovery
```

Isso resolve o pacote, gera `apm.lock.yaml` e projeta as primitives de `.apm/` nos diretórios do harness. Edite só a fonte em `.apm/`.

Neste repositório, depois do CLI no `PATH`:

```bash
apm install
apm compile
apm run lint
apm run test
apm run audit
apm run loop
```

## Mapa da descoberta

- [Pacote APM](docs/apm-setup.md)
- [Qualidade e segurança](docs/qualidade-seguranca.md)
- [Loop de entrega do agente](docs/agent-delivery-loop.md)
- [Amostra do loop](docs/agent-loop-sample.md)
- [Schemathesis](docs/schemathesis.md)
- [Checklist de produção](docs/production-checklist.md)
