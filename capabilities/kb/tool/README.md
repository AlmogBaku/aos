# aos-base — the kb capability's tool

Capability-shipped deterministic executor (ARCHITECTURE §2.4; RFC-004's outcome).
Installed at capability-install time:

    uv tool install --from <clone>/capabilities/kb/tool aos-base

…which puts the `base` command on PATH (recorded in the lockfile; removal =
`uv tool uninstall aos-base`). Zero-install alternative for one-off use:

    uvx --from <clone>/capabilities/kb/tool base --help

Judgment-free by contract: never calls an LLM, never invokes an agent; files and
exit codes are the interface. See the kb entry skill and design/kb-methodology.md §9.
