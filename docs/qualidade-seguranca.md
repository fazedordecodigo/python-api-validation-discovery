# Qualidade, segurança e práticas no harness

Esta página entra na mesma descoberta: desenvolvimento Python numa plataforma de dados na AWS. Além do contrato da API e da regra de negócio, o harness precisa barrar código frágil, segredo vazado e dependência vulnerável antes do merge.

Cada ferramenta abaixo roda duas vezes:

1. **Local**, como hook de pre-commit, para o autor ver a falha antes do push.
2. **De novo no CI** (GitHub Actions ou AWS CodeBuild), para o que passou por fora do hook não entrar.

Falha em qualquer uma bloqueia o merge. O hook local é conveniência. O CI é o gate.

## Ferramentas

| Ferramenta | Para que serve |
| --- | --- |
| Ruff ou Flake8 | Lint de Python. Estilo, imports mortos, erros comuns. Ruff cobre o papel do Flake8 com menos ferramentas soltas. Flake8 continua válido se o time já tem plugins nele. |
| mypy ou Pyright | Checagem de tipos. Pega contrato errado entre funções antes do runtime. mypy é o clássico. Pyright é o que o Pylance usa e costuma ser mais rápido. |
| Bandit | SAST em Python. Procura padrão inseguro no código (uso de `eval`, hash fraco, assert em código de segurança, subprocess com shell). Não substitui revisão. |
| gitleaks ou TruffleHog | Varredura de segredo no commit. Token, chave e senha no diff. gitleaks é o encaixe mais comum em pre-commit. TruffleHog olha também histórico e verificadores. |
| pip-audit ou Safety | Vulnerabilidade conhecida nas dependências Python (advisory no grafo do `pip`). pip-audit usa a base OSV/PyPI. Safety é a alternativa comercial com feed próprio. |
| Trivy | Scan de imagem Docker e de IaC da AWS (Terraform, CloudFormation, Dockerfile). Acha CVE na imagem e misconfig no que vai para a conta. |

## Onde cada uma entra

- Pre-commit: Ruff (ou Flake8), mypy ou Pyright, Bandit, gitleaks (ou TruffleHog), pip-audit (ou Safety).
- CI, de novo, as mesmas, mais Trivy na imagem e no IaC, porque imagem e template às vezes nem existem na máquina de quem commitou o Python.
- O pipeline que já roda Schemathesis e pytest-bdd ganha este estágio antes, ou em paralelo. Contrato e regra de negócio não substituem lint, tipo, SAST, segredo, dependência e imagem.

Nada disso decide a regra "acima de 10 mil exige aprovação". Isso continua no Gherkin. Isto aqui só garante que o código, o commit e o artefato que sobem para a AWS não carregam o erro mecânico que o harness consegue ver sem um humano.
