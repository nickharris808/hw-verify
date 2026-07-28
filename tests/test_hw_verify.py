"""The unified front end.

It is a delegating wrapper, so almost nothing here checks analysis behaviour — that
is the checkers' own test suites. What it checks is the two things a wrapper can get
wrong and thereby break the tools underneath it:

* **exit codes must pass through.** ctbench uses 2 for "no verdict", distinct from 1
  for "leaky". A wrapper that normalised those would let a CI job treat "we could not
  tell" as an ordinary failure, or as a pass.
* **arguments must pass through untouched**, including flags the wrapper itself would
  otherwise consume, like `--json`.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from hwverify_cli.main import TOOLS, main


def run(*args):
    return subprocess.run([sys.executable, "-m", "hwverify_cli.main", *args],
                          capture_output=True, text=True, check=False)


def test_bare_invocation_prints_help_and_succeeds():
    r = run()
    assert r.returncode == 0
    assert "hw-verify" in r.stdout


def test_every_declared_tool_actually_loads():
    """A verb pointing at a module that does not exist is a broken promise."""
    import importlib
    for verb, (module, dist, desc) in TOOLS.items():
        assert importlib.import_module(module), f"{verb} -> {module}"
        assert desc, verb
        assert dist


@pytest.mark.parametrize("verb", sorted(TOOLS))
def test_each_verb_delegates_its_help(verb):
    r = run(verb, "--help")
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip(), f"{verb} --help printed nothing"


def test_leaky_design_exits_1_through_the_wrapper(tmp_path):
    import ctbench
    fixtures = Path(ctbench.__file__).parent / "fixtures"
    (tmp_path / "leaky.v").write_text((fixtures / "cmp_leaky.v").read_text())
    r = subprocess.run([sys.executable, "-m", "hwverify_cli.main", "ct", "check",
                        "leaky.v", "--secret", "x", "--secret", "y"],
                       capture_output=True, text=True, cwd=tmp_path, check=False)
    assert r.returncode == 1, r.stdout + r.stderr


def test_unknown_exits_2_through_the_wrapper_not_1(tmp_path):
    """The distinction the wrapper must not flatten."""
    (tmp_path / "hier.v").write_text(
        "module top(clk,key,done); input clk; input [7:0] key; output done;\n"
        "  child u(.clk(clk),.key(key),.done(done));\nendmodule\n"
    )
    r = subprocess.run([sys.executable, "-m", "hwverify_cli.main", "ct", "check",
                        "hier.v", "--secret", "key"],
                       capture_output=True, text=True, cwd=tmp_path, check=False)
    assert r.returncode == 2, (
        f"expected 2 (no verdict), got {r.returncode} — the wrapper flattened the "
        f"distinction between 'leaky' and 'could not tell'"
    )


def test_clean_design_exits_0_through_the_wrapper(tmp_path):
    import ctbench
    fixtures = Path(ctbench.__file__).parent / "fixtures"
    (tmp_path / "clean.v").write_text((fixtures / "ct_cmp.v").read_text())
    r = subprocess.run([sys.executable, "-m", "hwverify_cli.main", "ct", "check",
                        "clean.v", "--secret", "x", "--secret", "y"],
                       capture_output=True, text=True, cwd=tmp_path, check=False)
    assert r.returncode == 0, r.stdout + r.stderr


def test_flags_the_wrapper_could_have_eaten_reach_the_tool(tmp_path):
    """`--json` is a plausible wrapper flag; it must belong to the tool."""
    import ctbench
    fixtures = Path(ctbench.__file__).parent / "fixtures"
    (tmp_path / "leaky.v").write_text((fixtures / "cmp_leaky.v").read_text())
    r = subprocess.run([sys.executable, "-m", "hwverify_cli.main", "ct", "check",
                        "leaky.v", "--secret", "x", "--secret", "y", "--json"],
                       capture_output=True, text=True, cwd=tmp_path, check=False)
    import json
    assert json.loads(r.stdout)["verdict"] == "LEAKY"


def test_mask_and_patch_verbs_run():
    assert run("mask", "corpus").returncode == 0
    assert run("patch", "check").returncode == 0


def test_an_unknown_verb_is_rejected():
    r = run("nonsense")
    assert r.returncode != 0
    assert "invalid choice" in r.stderr or "nonsense" in r.stderr


def test_version_is_reported():
    r = run("--version")
    assert r.returncode == 0
    assert "hw-verify" in r.stdout


def test_main_is_importable_and_returns_an_int():
    assert isinstance(main([]), int)
