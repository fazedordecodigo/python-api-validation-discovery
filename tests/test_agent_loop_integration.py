#!/usr/bin/env python3
"""Integração: loop completo na amostra de domínio."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
_SPEC = importlib.util.spec_from_file_location("agent_loop", SCRIPTS / "agent_loop.py")
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("não foi possível carregar scripts/agent_loop.py")
agent_loop = importlib.util.module_from_spec(_SPEC)
sys.modules["agent_loop"] = agent_loop
_SPEC.loader.exec_module(agent_loop)


def _have(*names: str) -> bool:
    return all(shutil.which(name) for name in names)


class SampleIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if not _have("ruff", "mypy", "pytest"):
            raise unittest.SkipTest("ruff, mypy e pytest precisam estar no PATH")

    def setUp(self) -> None:
        self.domain = ROOT / "sample" / "domain.py"
        self.limits = ROOT / "sample" / "limits.py"
        self.domain_orig = self.domain.read_text(encoding="utf-8")
        self.limits_orig = self.limits.read_text(encoding="utf-8")

    def tearDown(self) -> None:
        self.domain.write_text(self.domain_orig, encoding="utf-8")
        self.limits.write_text(self.limits_orig, encoding="utf-8")

    def _run_loop(self, agent: list[str]) -> tuple[int, str]:
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "agent_loop.py"),
                "--config",
                str(ROOT / "sample" / "loop.yaml"),
                "--changed-files",
                "sample/domain.py",
                "sample/limits.py",
                "--agent",
                " ".join(agent),
                "--root",
                str(ROOT),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        return proc.returncode, proc.stdout + proc.stderr

    def test_ruff_mypy_clean_domain_pytest_fails_then_mock_fixes(self) -> None:
        first = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "agent_loop.py"),
                "--config",
                str(ROOT / "sample" / "loop.yaml"),
                "--changed-files",
                "sample/domain.py",
                "sample/limits.py",
                "--root",
                str(ROOT),
            ],
            check=False,
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        text = first.stdout + first.stderr
        self.assertNotEqual(first.returncode, 0)
        self.assertIn("propriedade_quebrada:", text)
        self.assertIn("contraexemplo_minimo:", text)
        self.assertNotIn("Traceback (most recent call last)", text)

        code, out = self._run_loop([sys.executable, str(ROOT / "sample" / "mock_agent.py")])
        self.assertEqual(code, 0, out)
        self.assertIn("Volta em que passou:", out)
        self.assertIn("pytest-domain", out)
        self.assertIn("ruff", out)
        self.assertIn("mypy", out)
        self.assertIn("o que já passava continua passando", out)
        source = self.domain.read_text(encoding="utf-8")
        self.assertIn("amount > 10000", source)

    def test_repeated_hash_aborts_when_agent_does_not_fix(self) -> None:
        noop = (
            "import sys, pathlib, os\n"
            "print('noop agent')\n"
        )
        agent_path = ROOT / "sample" / "_noop_agent.py"
        agent_path.write_text(noop, encoding="utf-8")
        try:
            code, out = self._run_loop([sys.executable, str(agent_path)])
            self.assertEqual(code, 1, out)
            self.assertIn("mesmo hash de falha se repetiu", out)
        finally:
            agent_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
