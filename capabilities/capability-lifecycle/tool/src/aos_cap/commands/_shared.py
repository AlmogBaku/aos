"""What every command needs from the root `Typer()` callback: the one global option,
stashed on `ctx.obj` as `GlobalOpts` — and stashed RAW, unresolved. The callback never
calls `find_home()` itself; it only stores the string the user passed (or None).

That laziness is deliberate and load-bearing: `find_home()` rejects a household with no
`.aos/` directory, and `init` is the one verb that must accept one — it is what creates
the directory. An eager callback that resolved `--home` itself would reject a fresh
clone before `init`'s own body ever ran.

`GlobalOpts` keeps the attribute name `home` that `find_home()`/`find_home_soft()`
already read (they were written against an argparse `Namespace`), so passing a
`GlobalOpts` instance wherever the old code passed the namespace works with no change to
those functions."""

from dataclasses import dataclass

import typer

from ..constants import VERSION


@dataclass
class GlobalOpts:
    home: str | None = None


def version_callback(value: bool) -> None:
    if value:
        # argparse's `action="version"` prints to stdout and exits 0 immediately, before
        # subcommand dispatch — typer.echo() defaults to stdout too, and the eager option
        # fires before click even checks for a subcommand.
        typer.echo(f"aos-cap {VERSION}")
        raise typer.Exit()
