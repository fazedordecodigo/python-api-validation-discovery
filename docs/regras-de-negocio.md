# Regras de negócio em Gherkin

A regra de negócio não mora no OpenAPI. O spec descreve o contrato (rotas, schemas, status). O Gherkin descreve a regra, e o step chama a API de verdade.

Exemplo concreto: transferência acima de 10 mil exige aprovação.

```gherkin
Feature: Aprovação de transferência
  Scenario: Valor acima de 10 mil fica pendente de aprovação
    Given uma conta de origem com saldo de 50000 e limite diário de 100000
    And o usuário autenticado não tem alçada de aprovação
    When eu POST /transferencias com valor 10000.01, da conta origem para a conta destino
    Then a resposta é 202
    And o status da transferência é PENDENTE_APROVACAO
    And o saldo da origem não foi debitado
```

No pytest-bdd, o When faz o HTTP (httpx) e o Then lê status, body e o saldo de novo. Behave usa o mesmo formato de feature, com steps em Python puro.

A regra vira um cenário nomeado. O teste falha se a implementação debitar na hora ou devolver 200.

Esse cenário é um exemplo de domínio para a descoberta. A mesma estrutura vale para qualquer regra nomeada da plataforma de dados: pré-condição, chamada real, efeito observável (status, corpo e estado que não deveria mudar).
