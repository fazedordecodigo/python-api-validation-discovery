# Checklist de produção

Esta página lista o que ainda precisa valer antes de usar este harness em produção numa plataforma de dados na AWS com desenvolvimento Python. Não é um selo de pronto. Os itens marcados já valem em `scripts/agent_loop.py`. O restante continua aberto.

- [x] O loop só fecha quando o teste que falhava passa e os testes que já passavam continuam passando.
- [x] O hash do erro impede retentar o mesmo patch.
- [x] O feedback mínimo é a propriedade quebrada e o menor contraexemplo, não o log inteiro, e o modelo não é pedido para explicar o próprio erro.
- [x] O máximo de voltas é 3.
- [ ] Ruff e mypy entram no pre-commit. Bandit e gitleaks entram no CI.
- [ ] pip-audit e Trivy entram no pipeline de deploy.
- [ ] Schemathesis roda em job noturno. pytest-bdd roda no pull request.
- [ ] Segredo nunca fica no repositório, só em variável de ambiente.
