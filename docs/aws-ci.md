# CI na AWS

As duas camadas rodam no mesmo pipeline, contra a API publicada no API Gateway (stage de teste, não produção).

Opções de runner:

- **GitHub Actions:** o repositório do serviço dispara pytest (Schemathesis + pytest-bdd) com a URL do stage e o spec OpenAPI.
- **AWS CodeBuild:** o mesmo comando, se o padrão da plataforma já é build na AWS. O spec pode vir do artefato do build ou de um bucket.

O que o pipeline precisa ter:

- URL base do stage (API Gateway).
- Spec OpenAPI desse stage.
- Credencial de teste com escopo mínimo, em secret (Secrets Manager ou secret do Actions), nunca no repositório.
- Falha dura: Schemathesis divergiu do contrato, ou um cenário Gherkin nomeado falhou (status, corpo ou estado).

A regra dos 10 mil fica no arquivo `.feature`. O Then checa status 202, `PENDENTE_APROVACAO` e saldo não debitado. O Schemathesis não precisa conhecer essa frase. Ele só garante que o contrato da rota aguenta.
