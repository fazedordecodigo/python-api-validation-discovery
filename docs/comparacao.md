# Comparação

Contexto: desenvolvimento Python numa plataforma de dados na AWS. A pergunta é qual ferramenta garante que uma regra definida num spec (ou ao lado dele) está implementada.

| Ferramenta | O que faz bem | Limite |
| --- | --- | --- |
| pytest-bdd ou Behave | Python. A regra fica legível para quem define o domínio. O step chama a API. | Não gera casos a partir do OpenAPI. Cada regra é escrita. |
| Cucumber + REST Assured | Padrão quando o serviço já é Java. Gherkin na frente, HTTP no step. | Fora do fluxo Python desta descoberta, a menos que o serviço seja JVM. |
| Karate | HTTP e assert no mesmo DSL. Rápido para API. | Pior quando a regra precisa ser lida por quem não escreve o teste. |
| Gauge | Spec em Markdown, não em Gherkin. | Menos alinhado se o time já quer Given/When/Then. |
| Schemathesis | Gera casos do OpenAPI. Acha quebra de contrato. | Não cobre "acima de 10 mil exige aprovação" sozinho. |
| Dredd | Contrato simples, exemplo contra a API real. | Não faz fuzzing nem regra de negócio. |

Recomendação para este cenário Python:

1. Schemathesis na camada de contrato OpenAPI.
2. pytest-bdd na camada de regras nomeadas.
3. Dredd só se o time quiser um gate de contrato mais simples antes de investir em property-based.
