# Pacote APM deste harness

Esta página continua a descoberta: desenvolvimento Python numa plataforma de dados na AWS. O harness de qualidade, o loop de entrega e o Schemathesis ficam empacotados para o [Agent Package Manager](https://microsoft.github.io/apm/) da Microsoft, para o mesmo contexto chegar em mais de um agente.

Um pacote APM é `apm.yml` mais a árvore `.apm/`. Não há chave de topo `tools` no manifesto. Dependências de agente, scripts nomeados e primitives (skill, instruction, prompt) são os campos oficiais.

## Alvos

`apm.yml` declara `targets` nesta ordem:

1. `windsurf` (primeiro): alvo oficial do APM para o Devin Desktop e alvo primário deste pacote. O APM não tem outro slug para esse produto. Um valor de alvo desconhecido é erro de parse.
2. `claude`: Claude Code.
3. `cursor`
4. `copilot`

Não invente slug fora do catálogo do APM.

## O que o pacote contém

| Primitive | Caminho | Papel |
| --- | --- | --- |
| Skill | `.apm/skills/quality-security-loop/SKILL.md` | Quando fechar tarefa e quais checks do diff rodar. Aponta para `docs/qualidade-seguranca.md` e `docs/agent-delivery-loop.md`. |
| Skill | `.apm/skills/schemathesis-api/SKILL.md` | Quando a tarefa muda a API HTTP. Manda rodar Schemathesis no spec OpenAPI. |
| Instruction | `.apm/instructions/checks-must-pass.instructions.md` | Regra: a tarefa de código não termina enquanto os checks aplicáveis não passam. |
| Instruction | `.apm/instructions/schemathesis-openapi.instructions.md` | Nos arquivos OpenAPI: rode Schemathesis antes de fechar. |
| Prompt | `.apm/prompts/run-agent-loop.prompt.md` | Comando que o desenvolvedor invoca para rodar o loop. |

Scripts nomeados em `apm.yml` (`apm run <nome>`):

- `start`: amostra genérica com o agente substituto (`python3 scripts/agent_loop.py --demo`).
- `loop`: o wrapper no diff atual.
- `schemathesis`: `python3 -m schemathesis run {spec}`. Passe o spec com `--param spec=<caminho-ou-url>`.

A corrida ponta a ponta da regra nomeada usa `sample/loop.yaml` e `sample/mock_agent.py`, descrita em [Amostra do loop](agent-loop-sample.md).

Schemathesis é o validador de API HTTP deste harness. É a opção mais completa da descoberta: gera casos a partir do OpenAPI e procura quebra inesperada com fuzzing property-based. Complementa a camada de contrato e a camada de regra de domínio já descritas em `docs/schemathesis.md` e `docs/regras-de-negocio.md`. Como o manifesto não tem seção `tools`, o encaixe é o script `schemathesis` mais a skill e a instruction que impedem fechar uma mudança de API sem essa corrida.

## Instalar o APM

Siga o instalador oficial em [https://microsoft.github.io/apm/](https://microsoft.github.io/apm/):

```bash
curl -sSL https://aka.ms/apm-unix | sh
```

Em macOS com Homebrew: `brew install apm`. Outras opções (pip, Scoop, Windows) estão na mesma página.

## Instalar este pacote no repositório

Na raiz, depois do `apm` estar no `PATH`:

```bash
apm install
```

O manifesto já fixa `targets`. `apm install` valida `apm.yml`, publica o que está em `.apm/` (`includes: auto`) e projeta cada primitive nos diretórios do harness:

| Alvo | Skills | Prompts / commands | Instructions |
| --- | --- | --- | --- |
| `windsurf` (Devin Desktop, primário) | `.agents/skills/<nome>/SKILL.md` | `.windsurf/workflows/run-agent-loop.md` | `.windsurf/rules/` |
| `claude` (Claude Code) | `.claude/skills/<nome>/SKILL.md` | `.claude/commands/run-agent-loop.md` | `.claude/rules/` |
| `cursor` | `.agents/skills/<nome>/SKILL.md` | `.cursor/commands/run-agent-loop.md` | `.cursor/rules/` (`.mdc`) |
| `copilot` | `.agents/skills/<nome>/SKILL.md` | `.github/prompts/run-agent-loop.prompt.md` | `.github/instructions/` |

Edite só a fonte em `.apm/`. Rode `apm install` de novo para republicar. Não edite a cópia projetada.

Comandos úteis depois do install:

```bash
apm run start
apm run loop
apm run schemathesis --param spec=<caminho-ou-url-do-openapi>
```

O prompt `run-agent-loop` aparece no seletor de cada alvo (workflow no Windsurf, `/run-agent-loop` no Claude Code e no Cursor, picker de prompts no Copilot).

## Lockfile

`apm.lock.yaml` só deve existir se o CLI gerou. Este pacote não declara dependência APM remota.

Se `apm` não estiver instalado, ou se `apm install` não rodar limpo, não invente o lockfile. Instale o CLI e rode `apm install` neste repositório. O arquivo gerado pode ser commitado.

Nesta cópia de trabalho o CLI `apm` não estava no `PATH`. Por isso `apm.lock.yaml` não foi gerado nem commitado.

## Fora do APM

O wrapper e o mapa de checks não dependem do APM. Dá para rodar `python3 scripts/agent_loop.py --demo` como em [Amostra do loop](agent-loop-sample.md) sem instalar o CLI.
