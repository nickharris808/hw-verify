# hw-verify

**One install and one command for the whole toolkit: constant-time RTL, masking gadgets, and bounds-check patches.**

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](pyproject.toml)
[![CI](https://github.com/nickharris808/hw-verify/actions/workflows/ci.yml/badge.svg)](https://github.com/nickharris808/hw-verify/actions/workflows/ci.yml)

> **▶ [Try it in your browser](https://huggingface.co/spaces/nickh007/hw-verify)** — no install, nothing uploaded.

## Why this exists

The toolkit is five repositories, which is right for maintenance and wrong for
someone meeting it for the first time: discovering `ctbench`, then `ct-mask`, then
`patchproof` separately is three chances to give up. This installs all three and puts
one verb in front of each.

It is a **delegating** front end, not a reimplementation — each verb hands off to that
tool's own CLI with your arguments untouched. So there is exactly one implementation
of every flag, nothing to drift, and `hw-verify ct --help` shows ctbench's real help.

## Install

```bash
pip install git+https://github.com/nickharris808/hw-verify@main
```

That pulls `ctbench`, `ct-mask` and `patchproof` too. None of the four is on PyPI yet.

## 30-second quickstart

```bash
hw-verify ct check rtl/*.v --secret key        # timing leaks in RTL
hw-verify ct explain rtl/cmp.v --secret key    # ...and HOW the secret reaches it
hw-verify mask check dom_and                   # a masked gadget, probe by probe
hw-verify patch check                          # bounds-check patches, proved complete
```

## Worked example

```console
$ hw-verify ct check cmp_leaky.v
{
  "module": "cmp_leaky",
  "observation": "done",
  "secrets": ["x", "y"],
  "reaching_secrets": ["x", "y"],
  "verdict": "LEAKY",
  "cone_size": 9,
  "file": "cmp_leaky.v"
}
$ echo $?
1
```

Then ask *why*:

```console
$ hw-verify ct explain cmp_leaky.v
LEAKY — 'done' depends on x, y.

How each secret reaches it (shortest path first):

  x
  ├─ xr
  └─ done

  y
  ├─ yr
  └─ done
```

## The three verbs

| Verb | Question | Delegates to |
|---|---|---|
| `hw-verify ct` | Does a completion signal depend on a secret? | [`ctbench`](https://github.com/nickharris808/ctbench) |
| `hw-verify mask` | Is every probe of this masked gadget first-order independent? | [`ct-mask`](https://github.com/nickharris808/ct-mask) |
| `hw-verify patch` | Does this fix eliminate *every* violating input, not just the one you found? | [`patchproof`](https://github.com/nickharris808/patchproof) |

## Exit codes pass through unchanged

This matters more than it sounds. `ctbench` uses **three**:

| Exit | Meaning |
|---|---|
| `0` | constant-time |
| `1` | leaky |
| `2` | **no verdict** — the analysis could not read the design |

A wrapper that collapsed `2` into `1` would let a CI job treat *"we could not tell"*
as an ordinary failure, and a wrapper that collapsed it into `0` would treat it as a
pass. Neither is acceptable, so the codes are passed through untouched and there is a
test asserting exactly that.

## Honest scope

Each tool's own `SCOPE.md` is authoritative; this changes none of it.

- [ctbench SCOPE](https://github.com/nickharris808/ctbench/blob/main/SCOPE.md) — completion timing only, and the Verilog subset it can read
- [ct-mask SCOPE](https://github.com/nickharris808/ct-mask/blob/main/SCOPE.md) — glitch-free probing, first order, 2-share
- [patchproof SCOPE](https://github.com/nickharris808/patchproof/blob/main/SCOPE.md) — reachability in modelled bit semantics

**The commercial boundary**, unchanged: everything here analyses a design you hand it
in full. Proving a property to a third party who never receives the design is a
different problem and a commercial one.

## Development

```bash
pip install -e ".[dev]"
pytest tests -q && ruff check .
```

<!-- portfolio:start -->
## Part of the hw-verify toolkit

| Project | What it does |
|---|---|
| **▶ [Live demo](https://huggingface.co/spaces/nickh007/hw-verify)** | Constant-time checker in your browser |
| **`hw-verify`** (you are here) | One install, one command, all three checkers |
| [`ctbench`](https://github.com/nickharris808/ctbench) | Matched-pair constant-time RTL benchmark + leaderboard |
| [`patchproof`](https://github.com/nickharris808/patchproof) | Prove a bounds-check fix eliminates *every* violating input |
| [`patchproof-verify`](https://github.com/nickharris808/patchproof-verify) | Re-check its certificates in Rust, with no shared code |
| [`ct-mask`](https://github.com/nickharris808/ct-mask) | First-order masking verification by two certificates |
| [`hw-verify-mcp`](https://github.com/nickharris808/hw-verify-mcp) | MCP server — the checkers, callable by AI agents |
| [`ct-audit-action`](https://github.com/nickharris808/ct-audit-action) | GitHub Action — fail a PR on a leaky completion signal |
| [datasets](https://huggingface.co/datasets/nickh007/hw-verify) · [witness paths](https://huggingface.co/datasets/nickh007/hw-verify-paths) | Verdicts, and the reasoning behind them |
<!-- portfolio:end -->

## License

Apache-2.0. See [LICENSE](LICENSE).
