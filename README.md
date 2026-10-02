# Descoberta: validação de API em Python na AWS

Este repositório documenta uma descoberta para escolher a melhor forma de validar APIs num cenário de desenvolvimento **Python** numa **plataforma de dados na AWS**.

O objetivo não é adotar uma ferramenta agora. É separar duas perguntas que se misturam com facilidade:

1. O contrato OpenAPI está implementado?
2. A regra de negócio nomeada está implementada?

## Recomendação em duas camadas

- **Contrato:** [Schemathesis](https://github.com/schemathesis/schemathesis) gera casos a partir do OpenAPI (property-based / fuzzing) e acha quebra de contrato.
- **Regra de negócio:** [pytest-bdd](https://pytest-bdd.readthedocs.io/) (ou Behave) guarda a regra em Gherkin, legível para quem define o domínio, e o step chama a API de verdade.

Alternativa mais simples só para o contrato, quando o fuzzing ainda não compensa: [Dredd](https://github.com/apiaryio/dredd).

No CI da AWS, as duas camadas rodam no mesmo pipeline (CodeBuild ou GitHub Actions) contra a API publicada no API Gateway.

## Mapa

- [Schemathesis](docs/schemathesis.md)
- [Dredd](docs/dredd.md)
- [Regras de negócio em Gherkin](docs/regras-de-negocio.md)
- [Comparação de ferramentas](docs/comparacao.md)
- [CI na AWS](docs/aws-ci.md)
- [Qualidade e segurança no harness](docs/qualidade-seguranca.md)
- [Loop de entrega do agente](docs/agent-delivery-loop.md)
