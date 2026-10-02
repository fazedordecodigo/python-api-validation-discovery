# Dredd

Repositório: https://github.com/apiaryio/dredd

Dredd é a alternativa mais simples de teste de contrato. Ele lê o spec (API Blueprint ou OpenAPI) e confere se a API real responde como os exemplos e o contrato descrevem. Não gera uma explosão de casos property-based.

Quando preferir Dredd nesta descoberta:

- o spec já tem exemplos bons e o time quer um gate barato e fácil de ler;
- o objetivo é "a resposta bate com o exemplo", não "achar input que quebra o schema".

Quando preferir Schemathesis: o contrato é grande, os exemplos são poucos, e a pergunta é se a implementação aguenta o espaço de input que o OpenAPI declara.

Os dois podem coexistir. Dredd no caminho feliz documentado. Schemathesis no espaço do contrato.
