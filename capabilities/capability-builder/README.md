# capability-builder

Detects use-case-shaped requests mid-conversation and turns them
into an intake → research → design → approval → build procedure instead of ad hoc
changes to the harness; also evolves capabilities that already exist, scaled to how
much the change actually touches. This is the building-mode half of MARS — the
Mode-Aware Runtime System pattern (operating mode handles requests, building mode
designs capabilities) — per ARCHITECTURE §9, drafted but not yet landed on the
`spec` branch.

Spec one-pager: [capability-builder.md](https://github.com/AlmogBaku/aos/blob/spec/capabilities/capability-builder.md)

## Support matrix

| Harness | Status | Runner |
|---|---|---|
| Hermes | hook | @AlmogBaku |
| NanoClaw | unsupported (no runner yet) | — |
| OpenClaw | unsupported (no runner yet) | — |
