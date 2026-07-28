"""`hw-verify` — one command over the three checkers.

The portfolio is five repositories, which is right for maintenance and wrong for a
newcomer: discovering `ctbench`, then `ct-mask`, then `patchproof` separately is three
chances to stop. This installs all three and puts them behind one verb each.

It is deliberately a **delegating** front end, not a reimplementation. Each subcommand
hands off to the tool's own `main()` with the remaining arguments untouched, so there
is exactly one implementation of every flag and no second copy to drift. The cost is
that `hw-verify ct --help` shows `ctbench`'s help, which is the honest thing to show
anyway.

Two behaviours are load-bearing:

* **exit codes pass through unchanged.** `ctbench` uses 2 for "no verdict", distinct
  from 1 for "leaky", and a wrapper that flattened those would let a CI job treat
  "we could not tell" as a mere failure — or worse, as a pass.
* **a missing checker is a refusal, not a crash.** If a package is not installed the
  command says which one and how to get it, rather than surfacing an ImportError
  traceback.
"""

from __future__ import annotations

import argparse
import importlib
import sys

from . import __version__

# verb -> (module holding main(), distribution name, one-line description)
TOOLS: dict[str, tuple[str, str, str]] = {
    "ct": (
        "ctbench.cli",
        "ctbench",
        "constant-time RTL: does a completion signal depend on a secret?",
    ),
    "mask": (
        "ctmask.cli",
        "ct-mask",
        "masking gadgets: is every probe first-order independent of the secret?",
    ),
    "patch": (
        "patchproof.cli",
        "patchproof",
        "bounds-check fixes: does the patch eliminate *every* violating input?",
    ),
}

REPO = "https://github.com/nickharris808"

EPILOG = """
examples:
  hw-verify ct check rtl/*.v --secret key       check RTL for timing leaks
  hw-verify ct explain rtl/cmp.v --secret key   show HOW the secret reaches it
  hw-verify mask check dom_and                  analyse a masked gadget
  hw-verify patch check                         prove the modelled patches complete

Each verb delegates to that tool's own CLI, so `hw-verify ct --help` shows ctbench's
help and every flag behaves identically to running ctbench directly.

exit codes are passed through unchanged. ctbench in particular uses 2 for "no verdict
was reached", which is deliberately distinct from 1 for "leaky": a job guarding only
against 1 must not be satisfied by "we could not tell".

demo: https://huggingface.co/spaces/nickh007/hw-verify
"""


def _load(module: str, dist: str):
    """Import a checker's CLI, or explain how to install it."""
    try:
        return importlib.import_module(module)
    except ImportError:
        raise SystemExit(
            f"hw-verify: the {dist!r} package is not installed, so this command "
            f"cannot run.\n"
            f"           Install the whole toolkit:\n"
            f"             pip install git+{REPO}/hw-verify@main\n"
            f"           or just this checker:\n"
            f"             pip install git+{REPO}/{dist}@main"
        ) from None


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    p = argparse.ArgumentParser(
        prog="hw-verify",
        description="Prove security properties of hardware and bounds checks.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
    )
    p.add_argument("--version", action="version",
                   version=f"hw-verify {__version__}")
    p.add_argument(
        "tool", nargs="?", choices=sorted(TOOLS),
        help="; ".join(f"{k}: {v[2]}" for k, v in sorted(TOOLS.items())),
    )
    p.add_argument("args", nargs=argparse.REMAINDER,
                   help="arguments passed straight through to that tool")

    # Parse only the leading verb ourselves; everything after it belongs to the tool,
    # so it must not be interpreted here (a shared `--json` would otherwise be eaten).
    ns = p.parse_args(argv[:1] if argv and not argv[0].startswith("-") else argv)
    if ns.tool is None:
        p.print_help()
        return 0

    module, dist, _ = TOOLS[ns.tool]
    cli = _load(module, dist)
    rest = argv[1:]
    return int(cli.main(rest) or 0)


if __name__ == "__main__":
    sys.exit(main())
