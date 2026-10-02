# Schemathesis

Repositório: https://github.com/schemathesis/schemathesis

Schemathesis é uma ferramenta de teste de API property-based. Ela lê um spec OpenAPI (e também GraphQL) e gera casos com Hypothesis, inclusive bordas que um exemplo escrito à mão não cobre.

Serve para a primeira camada: **o contrato está implementado?** Status, schema do body, códigos documentados, combinações de input que o spec permite.

Não substitui uma regra de negócio nomeada. "Transferência acima de 10 mil exige aprovação" não está no OpenAPI a menos que você escreva o check na mão (hook, check customizado ou teste ao lado).

Uso típico nesta descoberta: apontar para o spec da API da plataforma de dados e falhar o pipeline quando a implementação diverge do contrato.
