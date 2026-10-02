#!/usr/bin/env python3
"""Testes unitários do wrapper: hash, feedback mínimo, globs e limite."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Mapping, Sequence

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
_SPEC = importlib.util.spec_from_file_location("agent_loop", SCRIPTS / "agent_loop.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("não foi possível carregar scripts/agent_loop.py")
agent_loop = importlib.util.module_from_spec(_SPEC)
sys.modules["agent_loop"] = agent_loop
_SPEC.loader.exec_module(agent_loop)


class FakeProcess(subprocess.CompletedProcess[str]):
    def __init__(self, returncode: int, stdout: str = "", stderr: str = "") -> None:
        super().__init__(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


class LoadConfigTests(unittest.TestCase):
    def test_root_loop_yaml_maps_quality_tools(self) -> None:
        config = agent_loop.load_config(ROOT / "loop.yaml")
        self.assertEqual(config.max_iterations, 3)
        names = [tool.name for tool in config.tools]
        self.assertEqual(
            names,
            ["ruff", "mypy", "bandit", "gitleaks", "pip-audit", "trivy"],
        )

    def test_sample_loop_yaml_selects_ruff_mypy_pytest(self) -> None:
        config = agent_loop.load_config(ROOT / "sample" / "loop.yaml")
        self.assertEqual([tool.name for tool in config.tools], ["ruff", "mypy", "pytest-domain"])


class SelectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = agent_loop.load_config(ROOT / "loop.yaml")

    def test_python_change_selects_lint_types_sast_and_secrets(self) -> None:
        changed = ["src/service.py"]
        selected = [
            tool.name
            for tool in self.config.tools
            if agent_loop.tool_applies(tool, changed)
        ]
        self.assertEqual(selected, ["ruff", "mypy", "bandit", "gitleaks"])

    def test_dependency_change_selects_audit_and_secrets(self) -> None:
        changed = ["requirements.txt"]
        selected = [
            tool.name
            for tool in self.config.tools
            if agent_loop.tool_applies(tool, changed)
        ]
        self.assertEqual(selected, ["gitleaks", "pip-audit"])

    def test_dockerfile_selects_trivy_and_secrets(self) -> None:
        changed = ["services/api/Dockerfile"]
        selected = [
            tool.name
            for tool in self.config.tools
            if agent_loop.tool_applies(tool, changed)
        ]
        self.assertEqual(selected, ["gitleaks", "trivy"])


class HashAndFeedbackTests(unittest.TestCase):
    def test_hash_uses_tool_normalized_message_and_check(self) -> None:
        first = agent_loop.hash_failure("pytest-domain", "Amount=10000.01\n", "pytest-domain")
        second = agent_loop.hash_failure("pytest-domain", "amount=10000.01\n\n", "pytest-domain")
        other = agent_loop.hash_failure("ruff", "amount=10000.01\n", "pytest-domain")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)
        self.assertEqual(len(first), 64)

    def test_extract_failure_prefers_labeled_property_and_example(self) -> None:
        output = (
            "long traceback that must not be the feedback\n"
            "propriedade: amount > 10000 implica PENDENTE_APROVACAO\n"
            "contraexemplo: 10000.01\n"
        )
        prop, example = agent_loop.extract_failure("pytest-domain", output)
        self.assertEqual(prop, "amount > 10000 implica PENDENTE_APROVACAO")
        self.assertEqual(example, "10000.01")
        self.assertNotIn("traceback", prop.lower())

    def test_format_feedback_is_property_plus_counterexample(self) -> None:
        result = agent_loop.CheckResult(
            tool="pytest-domain",
            check="pytest-domain",
            ok=False,
            output="RAW LOG " * 50,
            property_broken="amount > 10000 implica PENDENTE_APROVACAO",
            counterexample="10000.01",
            error_hash="abc",
        )
        text = agent_loop.format_feedback([result], 0)
        self.assertIn("propriedade_quebrada: amount > 10000 implica PENDENTE_APROVACAO", text)
        self.assertIn("contraexemplo_minimo: 10000.01", text)
        self.assertNotIn("RAW LOG", text)
        self.assertIn("Não explique o próprio erro", text)


class LoopBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = agent_loop.LoopConfig(
            max_iterations=3,
            tools=(
                agent_loop.ToolSpec(
                    name="ruff",
                    argv=("ruff", "check"),
                    apply=agent_loop.ApplyKind.PYTHON,
                    patterns=("**/*.py",),
                    pass_files=True,
                ),
            ),
        )

    def test_missing_tool_fails_clearly(self) -> None:
        def which(_name: str) -> str | None:
            return None

        def run(
            _argv: Sequence[str],
            _env: Mapping[str, str] | None,
            _stdin: str | None,
        ) -> subprocess.CompletedProcess[str]:
            raise AssertionError("não deve executar ferramenta ausente")

        code = agent_loop.run_loop(
            self.config,
            ["sample.py"],
            None,
            root=ROOT,
            which=which,
            run=run,
        )
        self.assertEqual(code, 1)

    def test_run_check_command_and_count_iterations_until_pass(self) -> None:
        calls: list[list[str]] = []
        state = {"dirty": True}

        def which(name: str) -> str | None:
            return f"/bin/{name}"

        def run(
            argv: Sequence[str],
            env: Mapping[str, str] | None,
            stdin_text: str | None,
        ) -> subprocess.CompletedProcess[str]:
            calls.append(list(argv))
            if argv[0].endswith("ruff"):
                if state["dirty"]:
                    return FakeProcess(
                        1,
                        stdout="sample.py:1:1: F401\npropriedade: import morto\ncontraexemplo: sample.py:1\n",
                    )
                return FakeProcess(0, stdout="ok\n")
            self.assertIn("propriedade_quebrada:", stdin_text or "")
            self.assertNotIn("F401 unused", stdin_text or "")
            state["dirty"] = False
            return FakeProcess(0, stdout="fixed\n")

        code = agent_loop.run_loop(
            self.config,
            ["sample.py"],
            ["demo"],
            root=ROOT,
            which=which,
            run=run,
        )
        self.assertEqual(code, 0)
        ruff_calls = [call for call in calls if call[0].endswith("ruff")]
        self.assertEqual(len(ruff_calls), 2)

    def test_max_iterations_aborts_at_three(self) -> None:
        def which(name: str) -> str | None:
            return f"/bin/{name}"

        n = {"i": 0}

        def run(
            argv: Sequence[str],
            _env: Mapping[str, str] | None,
            _stdin: str | None,
        ) -> subprocess.CompletedProcess[str]:
            if argv[0].endswith("ruff"):
                n["i"] += 1
                return FakeProcess(1, stdout=f"broken {n['i']}\n")
            return FakeProcess(0)

        code = agent_loop.run_loop(
            self.config,
            ["sample.py"],
            ["demo"],
            root=ROOT,
            which=which,
            run=run,
            max_iterations=3,
        )
        self.assertEqual(code, 1)
        self.assertEqual(n["i"], 4)

    def test_repeated_hash_discards_patch_and_aborts_line(self) -> None:
        def which(name: str) -> str | None:
            return f"/bin/{name}"

        def run(
            argv: Sequence[str],
            _env: Mapping[str, str] | None,
            _stdin: str | None,
        ) -> subprocess.CompletedProcess[str]:
            if argv[0].endswith("ruff"):
                return FakeProcess(
                    1,
                    stdout="propriedade: import morto\ncontraexemplo: sample.py:1\n",
                )
            return FakeProcess(0)

        code = agent_loop.run_loop(
            self.config,
            ["sample.py"],
            ["demo"],
            root=ROOT,
            which=which,
            run=run,
            max_iterations=3,
        )
        self.assertEqual(code, 1)

    def test_close_requires_fail_to_pass_and_pass_to_pass(self) -> None:
        baseline = {"ruff": True, "pytest-domain": False}
        passing = [
            agent_loop.CheckResult("ruff", "ruff", True, ""),
            agent_loop.CheckResult("pytest-domain", "pytest-domain", True, ""),
        ]
        regression = [
            agent_loop.CheckResult("ruff", "ruff", False, "lint"),
            agent_loop.CheckResult("pytest-domain", "pytest-domain", True, ""),
        ]
        still_failing = [
            agent_loop.CheckResult("ruff", "ruff", True, ""),
            agent_loop.CheckResult("pytest-domain", "pytest-domain", False, "rule"),
        ]
        self.assertTrue(agent_loop.can_close(baseline, passing))
        self.assertFalse(agent_loop.can_close(baseline, regression))
        self.assertFalse(agent_loop.can_close(baseline, still_failing))

    def test_rejects_unknown_apply(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.yaml"
            path.write_text(
                "max_iterations: 1\ntools:\n  - name: x\n    argv: [x]\n    apply: nope\n",
                encoding="utf-8",
            )
            with self.assertRaises(agent_loop.LoopError):
                agent_loop.load_config(path)


if __name__ == "__main__":
    unittest.main()
