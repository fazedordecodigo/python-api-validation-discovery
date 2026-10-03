# Pacote APM deste harness

Esta página continua a descoberta: desenvolvimento Python numa plataforma de dados na AWS. As validações de qualidade e segurança, o loop de entrega e o Schemathesis ficam empacotados para o [Agent Package Manager](https://microsoft.github.io/apm/) da Microsoft, para outro projeto instalar o mesmo contexto com `apm install`.

Um pacote APM é `apm.yml` mais a árvore `.apm/`. Não há chave de topo `tools` no manifesto. Dependências de agente, scripts nomeados e primitives (skill, instruction, prompt) são os campos oficiais. `apm-policy.yml` na raiz é a política deste repositório.

## Alvos

`apm.yml` declara só estes `targets`, nesta ordem:

1. `windsurf`: alvo oficial do APM para o Devin Desktop e alvo primário deste pacote. O APM não tem outro slug para esse produto. Um valor de alvo desconhecido é erro de parse.
2. `claude`: Claude Code.

Não invente slug fora do catálogo do APM (`copilot`, `claude`, `grok-build`, `cursor`, `opencode`, `codex`, `gemini`, `antigravity`, `windsurf`, `kiro`, `agent-skills`).

## O que o pacote contém

| Primitive | Caminho | Papel |
| --- | --- | --- |
| Skill | `.apm/skills/quality-security-loop/SKILL.md` | Quando fechar tarefa e quais checks do diff rodar. Aponta para `docs/qualidade-seguranca.md` e `docs/agent-delivery-loop.md`. |
| Skill | `.apm/skills/schemathesis-api/SKILL.md` | Quando a tarefa muda a API HTTP. Manda rodar Schemathesis no spec OpenAPI. |
| Instruction | `.apm/instructions/checks-must-pass.instructions.md` | Regra: a tarefa de código não termina enquanto os checks aplicáveis não passam. |
| Instruction | `.apm/instructions/security.instructions.md` | Bandit, pip-audit e Trivy nos arquivos que pedem esses checks. |
| Instruction | `.apm/instructions/secrets.instructions.md` | gitleaks em qualquer mudança. |
| Instruction | `.apm/instructions/schemathesis-openapi.instructions.md` | Nos arquivos OpenAPI: rode Schemathesis antes de fechar. |
| Prompt | `.apm/prompts/run-agent-loop.prompt.md` | Comando que o desenvolvedor invoca para rodar o loop. |

Scripts em `scripts/` e o mapa `scripts:` de `apm.yml` (`apm run <nome>`):

- `start`: amostra genérica com o agente substituto (`python3 scripts/agent_loop.py --demo`).
- `loop`: o wrapper no diff atual.
- `lint`: `sh scripts/lint.sh` — Ruff e mypy com os mesmos argv de `loop.yaml`.
- `test`: `sh scripts/test.sh` — unittest do harness.
- `audit`: `sh scripts/audit.sh` — Bandit, gitleaks, pip-audit e Trivy com os mesmos argv de `loop.yaml`.
- `schemathesis`: `python3 -m schemathesis run {spec}`. Passe o spec com `--param spec=<caminho-ou-url>`.

A corrida ponta a ponta da regra nomeada usa `sample/loop.yaml` e `sample/mock_agent.py`, descrita em [Amostra do loop](agent-loop-sample.md).

Schemathesis é o validador de API HTTP deste harness. Como o manifesto não tem seção `tools`, o encaixe é o script `schemathesis` mais a skill e a instruction que impedem fechar uma mudança de API sem essa corrida.

## Instalar o APM

Siga o instalador oficial em [https://microsoft.github.io/apm/](https://microsoft.github.io/apm/):

```bash
curl -sSL https://aka.ms/apm-unix | sh
```

Em macOS com Homebrew: `brew install apm`. Outras opções (pip, Scoop, Windows) estão na mesma página.

## Instalar este pacote noutro repositório

```bash
apm install fazedordecodigo/python-api-validation-discovery
```

Com caminho local:

```bash
apm install /caminho/para/python-api-validation-discovery
```

O CLI acrescenta o pacote em `dependencies.apm` do consumidor, resolve, varre as primitives e escreve `apm.lock.yaml`.

## Instalar neste repositório

Na raiz, depois do `apm` estar no `PATH`:

```bash
apm install
apm compile
```

O manifesto já fixa `targets`. `apm install` valida `apm.yml`, publica o que está em `.apm/` (`includes: auto`) e projeta cada primitive nos diretórios do harness:

| Alvo | Skills | Prompts / commands | Instructions |
| --- | --- | --- | --- |
| `windsurf` (Devin Desktop, primário) | `.agents/skills/<nome>/SKILL.md` | `.windsurf/workflows/run-agent-loop.md` | `.windsurf/rules/` |
| `claude` (Claude Code) | `.claude/skills/<nome>/SKILL.md` | `.claude/commands/run-agent-loop.md` | `.claude/rules/` |

Edite só a fonte em `.apm/`. Rode `apm install` de novo para republicar. Não edite a cópia projetada.

Comandos úteis depois do install:

```bash
apm run start
apm run loop
apm run lint
apm run test
apm run audit
apm run schemathesis --param spec=<caminho-ou-url-do-openapi>
```

O prompt `run-agent-loop` aparece no seletor de cada alvo (workflow no Windsurf, `/run-agent-loop` no Claude Code).

## Política

`apm-policy.yml` na raiz restringe os alvos a `windsurf` e `claude`, exige `description` e `license` no manifesto e não confia MCP transitivo. A descoberta automática de org não lê este arquivo; para o gate local use:

```bash
apm audit --ci --policy ./apm-policy.yml
```

## Lockfile

`apm.lock.yaml` só deve existir se o CLI gerou. Não escreva esse arquivo à mão.

Nesta cópia o arquivo foi gerado por `apm install` com o CLI APM 0.33.0. `apm_modules/` continua no `.gitignore`.

## Fora do APM

O wrapper e o mapa de checks não dependem do APM. Dá para rodar `python3 scripts/agent_loop.py --demo` como em [Amostra do loop](agent-loop-sample.md) sem instalar o CLI.
