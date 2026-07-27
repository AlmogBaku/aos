"""What every command needs from the root `Typer()` callback: the four global
options, stashed on `ctx.obj` as `GlobalOpts` — and stashed RAW, unresolved. The
callback never calls `Base()` or `resolve_principal()` itself; it only stores the
strings the user passed (or None).

That laziness is deliberate and load-bearing: `resolve_base()` (called downstream,
inside each command) rejects a layout 1 tree by design, and `kb migrate` is the one
verb that must accept one. An eager callback that resolved `--base` itself would
reject the tree before `migrate`'s own body ever ran — so `migrate` declares its own
local `--base` option instead of reading the global one, mirroring the old argparse
`dest="migrate_base"` shadow exactly.

`GlobalOpts` has the same attribute names (`base`, `registry`, `agent`, `principal`)
that `resolve_base()`/`acting()`/`agent_subject()`/`resolve_principal()` already read
via `getattr(x, "name", default)` — so passing a `GlobalOpts` instance wherever the
old code passed an argparse `Namespace` works with no change to those functions."""

from dataclasses import dataclass

import typer

from ..constants import VERSION, LAYOUT


@dataclass
class GlobalOpts:
    base: str | None = None
    registry: str | None = None
    agent: str | None = None
    principal: str | None = None


def version_callback(value: bool):
    if value:
        # argparse's `action="version"` prints to stdout and exits 0 immediately,
        # before subcommand dispatch — typer.echo() defaults to stdout too, and the
        # eager option below fires before click even checks for a subcommand.
        typer.echo(f"kb {VERSION} (layout {LAYOUT})")
        raise typer.Exit()
