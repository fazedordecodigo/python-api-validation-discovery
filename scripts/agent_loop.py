#!/usr/bin/env python3
"""Wrapper do loop de entrega do agente.

Lê o YAML de checks, escolhe ferramentas pelo glob do diff, devolve só a
propriedade quebrada e o menor contraexemplo, hasheia a falha e aborta a
linha se o mesmo hash voltar, e só fecha quando o que falhou passa e o que
já passava continua passando.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Never

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "loop.yaml"
DEFAULT_MAX_ITERATIONS = 3
DEMO_RELATIVE = Path("examples/loop-demo/work/sample.py")
DEMO_AGENT = ROOT / "scripts" / "demo_agent.py"
FEEDBACK_ENV = "AGENT_LOOP_FEEDBACK_FILE"
WORKDIR_ENV = "AGENT_LOOP_WORKDIR"
ITERATION_ENV = "AGENT_LOOP_ITERATION"

WhichFn = Callable[[str], str | None]
RunFn = Callable[[Sequence[str], Mapping[str, str] | None, str | None], subprocess.CompletedProcess[str]]


class ApplyKind(Enum):
    PYTHON = "python"
    PYTHON_CODE = "python_code"
    ALWAYS = "always"
    DEPENDENCIES = "dependencies"
    DOCKER_OR_IAC = "docker_or_iac"
    OPENAPI = "openapi"


@dataclass(frozen=True)
class ToolSpec:
    name: str
    argv: tuple[str, ...]
    apply: ApplyKind
    patterns: tuple[str, ...]
    pass_files: bool = True


@dataclass(frozen=True)
class LoopConfig:
    max_iterations: int
    tools: tuple[ToolSpec, ...]


@dataclass(frozen=True)
class CheckResult:
    tool: str
    check: str
    ok: bool
    output: str
    missing: bool = False
    skipped: bool = False
    property_broken: str = ""
    counterexample: str = ""
    error_hash: str = ""


@dataclass
class LoopState:
    seen_hashes: set[str] = field(default_factory=set)
    baseline_pass: dict[str, bool] = field(default_factory=dict)
    snapshot: dict[str, str] = field(default_factory=dict)
    aborted_line: bool = False


class LoopError(Exception):
    """Erro de uso ou de configuração do wrapper."""


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _parse_flow_sequence(text: str) -> list[object]:
    inner = text[1:-1].strip()
    if not inner:
        return []
    items: list[object] = []
    buf: list[str] = []
    quote = ""
    for char in inner:
        if quote:
            if char == quote:
                quote = ""
            buf.append(char)
            continue
        if char in {"'", '"'}:
            quote = char
            buf.append(char)
            continue
        if char == ",":
            item = "".join(buf).strip()
            if item:
                items.append(_parse_scalar(item))
            buf = []
            continue
        buf.append(char)
    tail = "".join(buf).strip()
    if tail:
        items.append(_parse_scalar(tail))
    return items


def _parse_scalar(raw: str) -> object:
    text = raw.strip()
    if not text:
        return ""
    if text[0] == "[" and text[-1] == "]":
        return _parse_flow_sequence(text)
    lowered = text.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in {"null", "~"}:
        return None
    if text.isdigit() or (text.startswith("-") and text[1:].isdigit()):
        return int(text)
    return _unquote(text)


def _strip_comment(line: str) -> str:
    quote = ""
    for index, char in enumerate(line):
        if quote:
            if char == quote:
                quote = ""
            continue
        if char in {"'", '"'}:
            quote = char
            continue
        if char == "#":
            return line[:index].rstrip()
    return line.rstrip()


def load_simple_yaml(text: str) -> object:
    """Carrega o subconjunto de YAML usado por loop.yaml (stdlib)."""

    lines = [_strip_comment(line) for line in text.splitlines()]
    filtered = [(number, line) for number, line in enumerate(lines, start=1) if line.strip()]

    def indent_of(line: str) -> int:
        return len(line) - len(line.lstrip(" "))

    def parse_block(index: int, min_indent: int) -> tuple[object, int]:
        if index >= len(filtered):
            return {}, index
        _number, line = filtered[index]
        if indent_of(line) < min_indent:
            return {}, index
        if line.lstrip().startswith("- "):
            return parse_list(index, indent_of(line))
        return parse_map(index, indent_of(line))

    def parse_map(index: int, expected: int) -> tuple[dict[str, object], int]:
        result: dict[str, object] = {}
        while index < len(filtered):
            number, line = filtered[index]
            indent = indent_of(line)
            if indent < expected:
                break
            if indent > expected:
                raise LoopError(f"indentação inválida na linha {number}")
            stripped = line.strip()
            if stripped.startswith("- "):
                break
            if ":" not in stripped:
                raise LoopError(f"esperado 'chave:' na linha {number}")
            key, rest = stripped.split(":", 1)
            key = key.strip()
            rest = rest.strip()
            index += 1
            if rest:
                result[key] = _parse_scalar(rest)
                continue
            if index >= len(filtered):
                result[key] = {}
                continue
            next_indent = indent_of(filtered[index][1])
            if next_indent <= expected:
                result[key] = {}
                continue
            value, index = parse_block(index, next_indent)
            result[key] = value
        return result, index

    def parse_list(index: int, expected: int) -> tuple[list[object], int]:
        result: list[object] = []
        while index < len(filtered):
            number, line = filtered[index]
            indent = indent_of(line)
            if indent < expected:
                break
            if indent > expected:
                raise LoopError(f"indentação inválida na linha {number}")
            stripped = line.strip()
            if not stripped.startswith("- "):
                break
            item_text = stripped[2:].strip()
            index += 1
            if not item_text:
                if index < len(filtered) and indent_of(filtered[index][1]) > expected:
                    value, index = parse_block(index, indent_of(filtered[index][1]))
                    result.append(value)
                else:
                    result.append({})
                continue
            if item_text.endswith(":") and not item_text.startswith("["):
                key = item_text[:-1].strip()
                nested: dict[str, object] = {}
                if index < len(filtered) and indent_of(filtered[index][1]) > expected:
                    value, index = parse_block(index, indent_of(filtered[index][1]))
                    nested[key] = value
                else:
                    nested[key] = {}
                result.append(nested)
                continue
            if ":" in item_text and not item_text.startswith("["):
                key, rest = item_text.split(":", 1)
                mapping: dict[str, object] = {key.strip(): _parse_scalar(rest.strip())}
                child_indent = expected + 2
                while index < len(filtered):
                    child_number, child_line = filtered[index]
                    child_indent_now = indent_of(child_line)
                    if child_indent_now <= expected:
                        break
                    child_stripped = child_line.strip()
                    if child_stripped.startswith("- "):
                        raise LoopError(
                            f"lista aninhada sem chave na linha {child_number}"
                        )
                    if ":" not in child_stripped:
                        raise LoopError(f"esperado 'chave:' na linha {child_number}")
                    child_key, child_rest = child_stripped.split(":", 1)
                    child_key = child_key.strip()
                    child_rest = child_rest.strip()
                    index += 1
                    if child_rest:
                        mapping[child_key] = _parse_scalar(child_rest)
                        continue
                    if (
                        index < len(filtered)
                        and indent_of(filtered[index][1]) > child_indent
                    ):
                        value, index = parse_block(index, indent_of(filtered[index][1]))
                        mapping[child_key] = value
                    else:
                        mapping[child_key] = {}
                result.append(mapping)
                continue
            result.append(_parse_scalar(item_text))
        return result, index

    if not filtered:
        return {}
    value, end = parse_block(0, indent_of(filtered[0][1]))
    if end != len(filtered):
        leftover = filtered[end][0]
        raise LoopError(f"conteúdo YAML não consumido a partir da linha {leftover}")
    return value


def load_config(path: Path) -> LoopConfig:
    raw = load_simple_yaml(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise LoopError(f"config inválida em {path}: esperado um mapa no topo")
    max_iterations = raw.get("max_iterations", DEFAULT_MAX_ITERATIONS)
    if not isinstance(max_iterations, int) or max_iterations < 1:
        raise LoopError("max_iterations deve ser um inteiro >= 1")
    tools_raw = raw.get("tools")
    if not isinstance(tools_raw, list) or not tools_raw:
        raise LoopError("tools deve ser uma lista não vazia")
    return LoopConfig(
        max_iterations=max_iterations,
        tools=tuple(_parse_tool(item) for item in tools_raw),
    )


def _parse_tool(item: object) -> ToolSpec:
    if not isinstance(item, dict):
        raise LoopError("cada entrada em tools deve ser um mapa")
    name = item.get("name")
    argv_raw = item.get("argv")
    apply_raw = item.get("apply")
    patterns_raw = item.get("patterns", [])
    pass_files = item.get("pass_files", True)
    if not isinstance(name, str) or not name:
        raise LoopError("tool.name é obrigatório")
    if not isinstance(argv_raw, list) or not argv_raw or not all(
        isinstance(part, str) for part in argv_raw
    ):
        raise LoopError(f"tool {name}: argv deve ser uma lista de strings")
    if not isinstance(apply_raw, str):
        raise LoopError(f"tool {name}: apply é obrigatório")
    try:
        apply = ApplyKind(apply_raw)
    except ValueError as exc:
        allowed = ", ".join(kind.value for kind in ApplyKind)
        raise LoopError(f"tool {name}: apply inválido {apply_raw!r}; use {allowed}") from exc
    if patterns_raw is None:
        patterns_raw = []
    if not isinstance(patterns_raw, list) or not all(
        isinstance(pattern, str) for pattern in patterns_raw
    ):
        raise LoopError(f"tool {name}: patterns deve ser uma lista de strings")
    if apply is not ApplyKind.ALWAYS and not patterns_raw:
        raise LoopError(f"tool {name}: patterns é obrigatório quando apply não é always")
    if not isinstance(pass_files, bool):
        raise LoopError(f"tool {name}: pass_files deve ser boolean")
    return ToolSpec(
        name=name,
        argv=tuple(argv_raw),
        apply=apply,
        patterns=tuple(patterns_raw),
        pass_files=pass_files,
    )


def normalize_rel(path: str | Path, root: Path) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return candidate.as_posix()
    return candidate.as_posix()


def discover_changed_files(root: Path, explicit: Sequence[str] | None, base: str) -> list[str]:
    if explicit:
        return sorted({normalize_rel(item, root) for item in explicit})
    names: set[str] = set()
    git = shutil.which("git")
    if git is None:
        raise LoopError("git não está instalado; passe --changed-files ou use --demo")
    try:
        base_diff = subprocess.run(
            [git, "-C", str(root), "diff", "--name-only", "--diff-filter=ACMR", base],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        raise LoopError(f"falha ao consultar o git: {exc}") from exc
    if base_diff.returncode != 0:
        detail = (base_diff.stderr or "").strip()
        message = f"git diff {base} saiu com código {base_diff.returncode}"
        if detail:
            message = f"{message}: {detail}"
        raise LoopError(message)
    names.update(_git_paths(base_diff.stdout, root))
    optional = (
        [git, "-C", str(root), "diff", "--name-only", "--cached", "--diff-filter=ACMR"],
        [git, "-C", str(root), "ls-files", "--others", "--exclude-standard"],
    )
    for command in optional:
        try:
            completed = subprocess.run(command, check=False, capture_output=True, text=True)
        except OSError as exc:
            raise LoopError(f"falha ao consultar o git: {exc}") from exc
        if completed.returncode != 0:
            continue
        names.update(_git_paths(completed.stdout, root))
    return sorted(names)


def _git_paths(stdout: str, root: Path) -> set[str]:
    names: set[str] = set()
    for line in stdout.splitlines():
        stripped = line.strip()
        if stripped:
            names.add(normalize_rel(stripped, root))
    return names


def match_patterns(path: str, patterns: Sequence[str]) -> bool:
    posix = path.replace("\\", "/")
    name = Path(posix).name
    for pattern in patterns:
        if fnmatch.fnmatch(posix, pattern) or fnmatch.fnmatch(name, pattern):
            return True
        if pattern.startswith("**/") and fnmatch.fnmatch(posix, pattern[3:]):
            return True
    return False


def _is_python_path(path: str) -> bool:
    return path.replace("\\", "/").endswith(".py")


def matching_files(tool: ToolSpec, changed: Sequence[str]) -> list[str]:
    if tool.apply is ApplyKind.ALWAYS:
        return list(changed)
    return [path for path in changed if match_patterns(path, tool.patterns)]


def tool_applies(tool: ToolSpec, changed: Sequence[str]) -> bool:
    kind = tool.apply
    if kind is ApplyKind.ALWAYS:
        return True
    if kind is ApplyKind.PYTHON or kind is ApplyKind.PYTHON_CODE:
        if any(_is_python_path(path) for path in changed):
            return True
        return bool(matching_files(tool, changed))
    if (
        kind is ApplyKind.DEPENDENCIES
        or kind is ApplyKind.DOCKER_OR_IAC
        or kind is ApplyKind.OPENAPI
    ):
        return bool(matching_files(tool, changed))
    unreachable: Never = kind
    raise LoopError(f"apply não tratado: {unreachable}")


def _one_process_per_file(kind: ApplyKind) -> bool:
    match kind:
        case ApplyKind.OPENAPI:
            return True
        case (
            ApplyKind.PYTHON
            | ApplyKind.PYTHON_CODE
            | ApplyKind.ALWAYS
            | ApplyKind.DEPENDENCIES
            | ApplyKind.DOCKER_OR_IAC
        ):
            return False
    unreachable: Never = kind
    raise LoopError(f"apply não tratado: {unreachable}")


def normalize_message(message: str) -> str:
    text = message.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r":\d+:\d+", ":N:N", text)
    text = re.sub(r":\d+", ":N", text)
    return text.strip().lower()


def hash_failure(tool: str, message: str, check: str) -> str:
    payload = f"{tool}\n{normalize_message(message)}\n{check}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def extract_failure(tool: str, output: str) -> tuple[str, str]:
    """Extrai propriedade quebrada e o menor contraexemplo. Não devolve o log cru."""

    labeled_prop = re.search(
        r"propriedade(?:_quebrada)?\s*:\s*([^;\n]+)", output, flags=re.IGNORECASE
    )
    labeled_ex = re.search(
        r"contraexemplo(?:_minimo)?\s*:\s*(\S+)", output, flags=re.IGNORECASE
    )
    if labeled_prop and labeled_ex:
        return labeled_prop.group(1).strip(), labeled_ex.group(1).strip()

    failed = re.search(r"FAILED\s+(\S+)", output)
    amount = re.search(r"\b(\d+\.\d+|\d+)\b", output)
    status = re.search(r"(PENDENTE_APROVACAO|REJEITADA|APROVADA)", output)
    path_hit = re.search(r"([\w./\\-]+\.py:\d+(?::\d+)?)", output)
    ruff_code = re.search(r"\b([A-Z]\d{3,4})\b", output)

    if failed:
        property_broken = f"o teste {failed.group(1)} deve passar"
        if status:
            property_broken = (
                f"status deve ser {status.group(1)} quando a regra nomeada quebra"
            )
        example = amount.group(1) if amount else failed.group(1)
        return property_broken, example

    if ruff_code and path_hit:
        return f"{tool} {ruff_code.group(1)} deve ficar limpo", path_hit.group(1)
    if path_hit:
        return f"{tool} deve passar no arquivo tocado", path_hit.group(1)

    first = next((line.strip() for line in output.splitlines() if line.strip()), tool)
    first = re.sub(r"^E\s+", "", first)
    return f"{tool} deve satisfazer: {first[:160]}", first[:80]


def format_feedback(results: Sequence[CheckResult], iteration: int) -> str:
    lines = [
        f"Iteração {iteration}.",
        "Corrija a propriedade quebrada. Não explique o próprio erro.",
        "Não desligue o check com noqa, type: ignore ou baseline.",
        "",
    ]
    for result in results:
        if result.skipped or result.ok:
            continue
        lines.append(f"check: {result.check}")
        lines.append(f"propriedade_quebrada: {result.property_broken}")
        lines.append(f"contraexemplo_minimo: {result.counterexample}")
        lines.append("")
    text = "\n".join(lines).rstrip() + "\n"
    if "Traceback" in text or len(text) > 2000:
        raise LoopError("feedback mínimo ultrapassou o contrato (log cru)")
    return text


def default_which(program: str) -> str | None:
    if os.path.sep in program or (os.path.altsep and os.path.altsep in program):
        path = Path(program)
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)
        return None
    return shutil.which(program)


def default_run(
    argv: Sequence[str],
    env: Mapping[str, str] | None,
    stdin_text: str | None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    cwd = None
    if env and "PWD" in env:
        cwd = env["PWD"]
    return subprocess.run(
        list(argv),
        check=False,
        capture_output=True,
        text=True,
        env=merged,
        input=stdin_text,
        cwd=cwd,
    )


def expand_argv(argv: Sequence[str], files: Sequence[str]) -> list[str]:
    expanded: list[str] = []
    replaced = False
    for part in argv:
        if part == "{files}":
            expanded.extend(files)
            replaced = True
        else:
            expanded.append(part)
    if not replaced:
        expanded.extend(files)
    return expanded


def _execute_check(
    tool: ToolSpec,
    check: str,
    argv: Sequence[str],
    *,
    root: Path,
    run: RunFn,
) -> CheckResult:
    try:
        completed = run(argv, {"PWD": str(root)}, None)
    except OSError as exc:
        message = f"{tool.name}: falha ao executar {argv[0]}: {exc}"
        return CheckResult(
            tool=tool.name,
            check=check,
            ok=False,
            output=message,
            property_broken=f"{tool.name} deve executar",
            counterexample=str(exc),
            error_hash=hash_failure(tool.name, message, check),
        )
    output = (completed.stdout or "") + (completed.stderr or "")
    ok = completed.returncode == 0
    property_broken = ""
    counterexample = ""
    digest = ""
    if not ok:
        property_broken, counterexample = extract_failure(tool.name, output)
        digest = hash_failure(tool.name, f"{property_broken}|{counterexample}", check)
    return CheckResult(
        tool=tool.name,
        check=check,
        ok=ok,
        output=output.strip(),
        property_broken=property_broken,
        counterexample=counterexample,
        error_hash=digest,
    )


def run_tool(
    tool: ToolSpec,
    changed: Sequence[str],
    *,
    root: Path,
    which: WhichFn,
    run: RunFn,
) -> list[CheckResult]:
    if not tool_applies(tool, changed):
        return [
            CheckResult(tool=tool.name, check=tool.name, ok=True, output="", skipped=True)
        ]
    files = matching_files(tool, changed)
    resolved = which(tool.argv[0])
    if resolved is None:
        message = (
            f"{tool.name}: ferramenta não instalada ({tool.argv[0]}). "
            "O loop não trata ausência como sucesso. Instale o binário e rode de novo."
        )
        return [
            CheckResult(
                tool=tool.name,
                check=tool.name,
                ok=False,
                output=message,
                missing=True,
                property_broken=f"{tool.name} precisa estar instalado",
                counterexample=tool.argv[0],
                error_hash=hash_failure(tool.name, message, tool.name),
            )
        ]
    argv = [resolved, *tool.argv[1:]]
    if not tool.pass_files:
        return [_execute_check(tool, tool.name, argv, root=root, run=run)]
    if not files:
        return [
            CheckResult(tool=tool.name, check=tool.name, ok=True, output="", skipped=True)
        ]
    if _one_process_per_file(tool.apply):
        return [
            _execute_check(
                tool,
                f"{tool.name}[{path}]",
                expand_argv(argv, [path]),
                root=root,
                run=run,
            )
            for path in files
        ]
    return [_execute_check(tool, tool.name, expand_argv(argv, files), root=root, run=run)]


def snapshot_paths(root: Path, changed: Sequence[str]) -> dict[str, str]:
    snap: dict[str, str] = {}
    candidates = {normalize_rel(path, root) for path in changed}
    sample_dir = root / "sample"
    if sample_dir.is_dir():
        for path in sample_dir.rglob("*.py"):
            candidates.add(normalize_rel(path, root))
    for rel in candidates:
        full = root / rel
        if full.is_file():
            snap[rel] = full.read_text(encoding="utf-8")
    return snap


def restore_snapshot(root: Path, snap: Mapping[str, str]) -> None:
    for rel, content in snap.items():
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def split_agent_command(command: str) -> list[str]:
    parts = shlex.split(command, posix=os.name != "nt")
    if not parts:
        raise LoopError("comando do agente vazio")
    return parts


def run_agent(
    agent_argv: Sequence[str],
    feedback: str,
    *,
    root: Path,
    iteration: int,
    run: RunFn,
    which: WhichFn,
) -> subprocess.CompletedProcess[str]:
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        prefix="agent-loop-feedback-",
        suffix=".txt",
        delete=False,
    ) as handle:
        handle.write(feedback)
        feedback_path = handle.name
    env = {
        FEEDBACK_ENV: feedback_path,
        WORKDIR_ENV: str(root),
        ITERATION_ENV: str(iteration),
    }
    argv = [part.replace("{feedback}", feedback_path) for part in agent_argv]
    resolved = which(argv[0])
    if resolved is None:
        raise LoopError(
            f"comando do agente não encontrado: {argv[0]}. "
            "Passe um executável instalado ou use --demo."
        )
    argv = [resolved, *argv[1:]]
    try:
        return run(argv, env, feedback)
    finally:
        Path(feedback_path).unlink(missing_ok=True)


def seed_demo_fixture(root: Path) -> Path:
    target = root / DEMO_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "import json\n\n\ndef greet(name: str) -> str:\n    return f\"hello {name}\"\n",
        encoding="utf-8",
    )
    return target


def record_baseline(results: Sequence[CheckResult]) -> dict[str, bool]:
    return {
        result.check: result.ok
        for result in results
        if not result.skipped
    }


def can_close(baseline: Mapping[str, bool], results: Sequence[CheckResult]) -> bool:
    current = {result.check: result for result in results if not result.skipped}
    if any(not result.ok for result in current.values()):
        return False
    for check, passed in baseline.items():
        now = current.get(check)
        if now is None:
            return False
        if passed and not now.ok:
            return False
        if (not passed) and not now.ok:
            return False
    return True


def report_success(results: Sequence[CheckResult], iteration: int) -> str:
    ran = [result.check for result in results if not result.skipped]
    skipped = [result.check for result in results if result.skipped]
    lines = [
        "Loop encerrado: o que falhava passou e o que já passava continua passando.",
        f"Volta em que passou: {iteration}.",
        f"Checks rodados: {', '.join(ran) if ran else '(nenhum)'}.",
    ]
    if skipped:
        lines.append(f"Checks fora deste diff: {', '.join(skipped)}.")
    return "\n".join(lines)


def run_loop(
    config: LoopConfig,
    changed: Sequence[str],
    agent_argv: Sequence[str] | None,
    *,
    root: Path,
    which: WhichFn = default_which,
    run: RunFn = default_run,
    max_iterations: int | None = None,
) -> int:
    limit = max_iterations if max_iterations is not None else config.max_iterations
    if limit < 1:
        raise LoopError("max_iterations deve ser >= 1")
    state = LoopState(snapshot=snapshot_paths(root, changed))
    iteration = 0
    last_results: list[CheckResult] = []
    while True:
        last_results = [
            result
            for tool in config.tools
            for result in run_tool(tool, changed, root=root, which=which, run=run)
        ]
        if not state.baseline_pass:
            state.baseline_pass = record_baseline(last_results)
        failed = [result for result in last_results if not result.ok and not result.skipped]
        if not failed and can_close(state.baseline_pass, last_results):
            print(report_success(last_results, iteration))
            return 0
        if not failed and not can_close(state.baseline_pass, last_results):
            print(
                "Loop parado: houve verde parcial, mas um check que já passava "
                "não foi reconfirmado.\n"
            )
            return 1
        repeated = [
            result for result in failed if result.error_hash in state.seen_hashes
        ]
        for result in failed:
            if result.error_hash:
                state.seen_hashes.add(result.error_hash)
        if repeated:
            restore_snapshot(root, state.snapshot)
            state.aborted_line = True
            print(
                "Loop parado: o mesmo hash de falha se repetiu; "
                "o patch desta linha foi descartado.\n",
                format_feedback(last_results, iteration),
                sep="",
            )
            return 1
        if iteration >= limit:
            restore_snapshot(root, state.snapshot)
            print(
                "Loop parado: limite de voltas atingido.\n",
                format_feedback(last_results, iteration),
                sep="",
            )
            return 1
        if agent_argv is None:
            print(
                "Checks falharam e nenhum comando de agente foi passado.\n",
                format_feedback(last_results, iteration),
                sep="",
            )
            return 1
        pre_patch = snapshot_paths(root, changed)
        feedback = format_feedback(last_results, iteration)
        print(feedback)
        print(f"Chamando o agente (volta {iteration + 1}/{limit})...")
        try:
            agent_result = run_agent(
                agent_argv,
                feedback,
                root=root,
                iteration=iteration + 1,
                run=run,
                which=which,
            )
        except LoopError as exc:
            print(str(exc))
            return 1
        if agent_result.returncode != 0:
            restore_snapshot(root, pre_patch)
            print(
                "O comando do agente saiu com erro; o patch foi revertido.\n"
                f"{agent_result.stdout}{agent_result.stderr}"
            )
            return 1
        if agent_result.stdout:
            print(agent_result.stdout.rstrip())
        iteration += 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Roda os checks aplicáveis ao diff e devolve ao agente só a "
            "propriedade quebrada e o menor contraexemplo."
        )
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="YAML com o mapa ferramenta/padrão (padrão: loop.yaml)",
    )
    parser.add_argument(
        "--agent",
        help="Comando do agente de código. Use --demo para o substituto local.",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=None,
        help="Máximo de correções do agente (padrão: valor do config, 3).",
    )
    parser.add_argument(
        "--changed-files",
        nargs="+",
        help="Lista explícita de arquivos mudados. Sem isso, o wrapper lê o git.",
    )
    parser.add_argument(
        "--base",
        default="HEAD",
        help="Ref do git para o diff (padrão: HEAD).",
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Semeia um fixture e usa scripts/demo_agent.py no lugar de um agente real.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help="Raiz do repositório (padrão: pai de scripts/).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        config = load_config(args.config)
        agent_argv: list[str] | None
        if args.demo:
            sample = seed_demo_fixture(root)
            changed = [normalize_rel(sample, root)]
            agent_argv = [sys.executable, str(DEMO_AGENT)]
        else:
            changed = discover_changed_files(root, args.changed_files, args.base)
            agent_argv = split_agent_command(args.agent) if args.agent else None
        if not changed and not args.demo:
            print("Nenhum arquivo mudado no diff. Só os checks always (segredo) rodam.")
        return run_loop(
            config,
            changed,
            agent_argv,
            root=root,
            max_iterations=args.max_iterations,
        )
    except LoopError as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
