---
allowed-tools:
- Bash
- Read
- Grep
argument-hint: <agent>
arguments:
- agent
description: Roda o wrapper do loop de entrega do agente nos arquivos da mudança.
---

# Rodar o loop de entrega

Execute o wrapper deste repositório. Não declare a tarefa pronta antes dos checks aplicáveis passarem.

Fonte da verdade para o que deve rodar: `docs/agent-delivery-loop.md` e `docs/qualidade-seguranca.md`. O mapa concreto está em `loop.yaml`.

1. Se `$agent` estiver vazio, rode a amostra sem agente real:

```bash
python3 scripts/agent_loop.py --demo
```

2. Se `$agent` tiver um comando, use-o:

```bash
python3 scripts/agent_loop.py --agent "$agent"
```

3. Leia a saída. Passou: relate checks rodados, volta em que passou e o comando. Falhou: corrija só o que a saída aponta e rode de novo, até o limite de 3 voltas.
4. Se a mudança for de API HTTP, depois do loop rode Schemathesis no spec OpenAPI (`apm run schemathesis --param spec=<openapi>`). Veja `docs/schemathesis.md`.
5. Não desligue check com `noqa` ou `type: ignore` para forçar o verde.