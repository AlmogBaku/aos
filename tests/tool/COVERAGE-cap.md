# `aos-cap` contract coverage

The index of what `tests/tool/test_cap.py` guards, written **before** the suite was
rebuilt on `typer.testing.CliRunner` so a from-scratch rewrite could be diffed against it
mechanically rather than trusted:

```bash
grep -o '^- \[ \] test_\w*' tests/tool/COVERAGE-cap.md | sed 's/^- \[ \] //' | sort > /tmp/want.txt
grep -o '    def test_\w*' tests/tool/test_cap.py | sed 's/.*def //' | sort > /tmp/have.txt
comm -23 /tmp/want.txt /tmp/have.txt        # must print nothing
```

Rows began as the pre-rewrite suite's **81** tests: 40 happy-path (exit 0 only) and 41 that
pin a non-zero exit. Per code: **1** generic → 8 · **12** manifest invalid → 10 · **13**
drift → 3 · **14** no such entry → 3 · **15** no home → 4 · **16** artifact missing → 4 ·
**17** name collision → 9. Sections added since carry their own counts — the console-script
smoke tests the rewrite added, and the **18** name-slot family — so the file stays a
complete index of the suite.

Rows tagged **PIN** are regression pins for real bugs that shipped. Their one-line "why"
is the point of the row — a rewrite that drops one re-opens the bug, and a rewrite that
keeps the assertion but loses the reason invites a later reader to "simplify" it away.

## The surface: 12 verbs + `--version`

| verb | promises | exits |
|---|---|---|
| `manifest <dir>` | parse + validate a `CAPABILITY.md` (§2.2), emit it as JSON on stdout | 0, 12 |
| `skills <dir>` | every skill's **installed** name (`<prefix><id>`, entry skill verbatim); `--json` adds the prefix; `--check` **is** the collision gate and names the sources it consulted | 0, 12, 15, 17, 1 |
| `agents <dir>` | every agent's **installed** name (`<skill_prefix><agent-id>`, from `agents/*.agent.yaml`); `--json` adds the prefix; `--check` is the same single-owner gate over the agent namespace, against **two** of three sources — and names the third it cannot reach | 0, 12, 15, 17 |
| `render <dir> <skill> --out` | copy `skills/<id>/` to `<out>/<installed-name>/`, rewrite `name`, stamp `metadata.aos.origin`, resolve the `{{skill:}}`/`{{agent:}}` name slots; mechanical + idempotent | 0, 1, 12, 14, 18 |
| `home` | print the resolved household root | 0, 15 |
| `init` | create an empty `<home>/.aos/installs.lock.yaml`; the one verb that may find no `.aos/` | 0, 1, 15 |
| `record <cap> --version` | write one capability's entry: artifact sha256s, link targets, source root, jobs, config keys, env-var names, scripts | 0, 15, 16 |
| `rehash <cap>` | re-hash the recorded artifacts in place after an approved evolve | 0, 14, 15, 16 |
| `verify [<cap>]` | re-hash artifacts and re-read links against disk | 0, 13, 14, 15 |
| `show <cap>` | print one entry as JSON | 0, 14, 15 |
| `list` | installed capabilities + versions + counts | 0, 15 |
| `remove <cap>` | drop one entry (after the removal walk) | 0, 14, 15 |
| `--version` | `aos-cap <version>`, eager, before subcommand dispatch | 0 |

Global, and it goes **before** the verb: `--home` (else `$AOS_HOME`, else a cwd-upward
`.aos/` search — and for `skills --check`, also a search upward from the capability dir).

## `manifest` — 10

Happy path: a valid package prints its frontmatter as JSON with `id` and `version` intact.

- [ ] test_manifest_valid_prints_json — 0; JSON on stdout, `id` + `version` round-trip
- [ ] test_manifest_x_fields_allowed — 0; `x-*` is the third-party namespace in **our** schema
- [ ] test_manifest_accepts_all_shipped_capabilities — 0; drift guard: the tool must accept every in-repo `CAPABILITY.md` the tier-1 lint accepts
- [ ] test_depends_resolves_across_the_two_household_roots — **PIN**; 0; the check was `cap_dir.parent / dep`, the sibling root only, so a `personal/` capability depending on an `upstream/` one failed validation on a **correct** declaration. One resolver (`names.resolve_capability`) now serves this and slot resolution, so the two cannot disagree about where a capability lives
- [ ] test_manifest_unknown_key_rejected — 12; rule of two: an undeclared key is an error, and the message names it
- [ ] test_manifest_bad_version_rejected — 12; version must be MAJOR.MINOR.PATCH
- [ ] test_manifest_undeclared_skill_dir_rejected — 12; an on-disk `skills/<id>/SKILL.md` nobody declared would still install
- [ ] test_manifest_schedule_and_depends_rules — 12; one invocation reports **all** four problems (missing dependency, schedule `id`, `prompt_ref` for the agent form, required `degraded`) — an installer fixing a manifest wants every error at once, not the first
- [ ] test_manifest_malformed_shapes_exit_12 — 12; `depends:`/`schedules:` of the wrong YAML *shape* is a clean error, never a traceback
- [ ] test_manifest_scalar_frontmatter_exit_12 — 12; frontmatter that is a scalar, not a mapping, likewise

## `skills` — the installed name and the collision gate — 30

Happy path: one `id\tinstalled_name\tused_by` row per declared skill; `--check` adds
`clean: N skill names unclaimed` plus a `checked:` line per source consulted.

### the naming algorithm (§2.5) — 7

- [ ] test_prefix_defaults_to_capability_id — 0; absent `skill_prefix` means `<id>-`
- [ ] test_declared_prefix_wins — 0
- [ ] test_entry_skill_installs_verbatim — 0; the skill named after its capability is never prefixed
- [ ] test_already_prefixed_id_is_not_double_prefixed — 0
- [ ] test_empty_prefix_falls_back_to_default — 0; `skill_prefix: ""` is absent, not a format error
- [ ] test_json_reports_prefix_and_rows — 0; `--json` carries `skill_prefix` + ordered `installed_name`s
- [ ] test_relative_capability_dir_works — 0; `aos-cap skills .` from inside the package — the contract's commands are written with `<cap-dir>` paths, so a relative one must not break the `id == dirname` check

### name validation, against the INSTALLED name — 4

- [ ] test_malformed_prefix_rejected — 12; `Demo_` is not `[a-z0-9-]`
- [ ] test_prefix_without_trailing_hyphen_rejected — 12
- [ ] test_over_long_installed_name_rejected — 12; an id that fits alone can exceed the Agent Skills max 64 **once prefixed** — the shipped identity carries the limit
- [ ] test_reserved_word_in_installed_name_rejected — 12; `claude`/`anthropic` are reserved

### the gate says no — exit 17 — 8

- [ ] test_collision_with_another_household_capability — 17; another capability in `personal/` already claims the name
- [ ] test_collision_inside_one_capability — 17; the entry skill's name reached a second time through the prefix ("...in itself")
- [ ] test_collision_with_a_lockfile_link — 17; a lockfile link attributes the name to another install
- [ ] test_collision_with_a_skill_already_in_the_harness — 17
- [ ] test_flat_harness_skill_file_also_collides — 17; Nanobot's `skills/<name>.md` flat form is a claim too
- [ ] test_a_skill_merely_MENTIONING_the_origin_key_is_not_claimed_as_ours — **PIN**; 17; the gate used to test `ORIGIN_KEY in text` — a **substring** — so a stranger's skill whose *prose* discussed `metadata.aos.origin` read as aos-installed, and the install overwrote it instead of stopping. Provenance is read as structured frontmatter or it does not claim the entry
- [ ] test_collision_found_when_cwd_is_outside_the_household — **PIN**; 17; on a real machine the agent's cwd is the harness workspace and no documented invocation passes `--home`. Resolving the household from cwd alone made `--check` skip the household + lockfile sources and still print "clean" — a silent no-op in the gate. Discovery now also walks up from the capability dir
- [ ] test_another_capabilitys_flat_form_link_still_collides — **PIN**; 17; the mirror of the flat-form exemption below: a `.md` link owned by someone **else** is still a claim, so all three comparison sites have to agree on stems

### the gate says yes, for the right reason — 10

- [ ] test_clean_check_reports_unclaimed — 0; the clean report counts the names it cleared
- [ ] test_reinstall_over_our_own_links_is_clean — 0; a re-install is not a collision with itself
- [ ] test_non_skill_link_is_not_a_skill_name — 0; a linked *script*'s basename is not a skill name
- [ ] test_malformed_neighbour_does_not_block_the_check — 0; a broken `CAPABILITY.md` next door must not abort an unrelated install
- [ ] test_readme_in_a_flat_skills_dir_is_not_a_skill — 0; `README.md` in a flat skills dir is documentation
- [ ] test_reinstall_over_our_own_flat_form_link_is_clean — 0; Nanobot's flat form records a link whose basename carries `.md`, and it still has to match our own exemption (`.stem`, not `.name`)
- [ ] test_lost_lockfile_does_not_block_reinstall — **PIN**; 0; `.aos/` is machine-local and gitignored. A gate that trusted it alone saw our own installed skills as strangers and refused **every** re-install — turning a recoverable state into a stuck one. Provenance answers when the lockfile cannot
- [ ] test_a_stranger_still_blocks_when_the_lockfile_is_lost — **PIN**; 17; the other half of that fallback: provenance exempts our renders, not every name in the directory
- [ ] test_clean_report_names_the_sources_it_could_not_check — **PIN**; 0; a skipped source must never be indistinguishable from an empty one, so the report says `NO HOUSEHOLD RESOLVED` / `NO --harness-skills GIVEN` in as many words
- [ ] test_clean_report_names_the_sources_it_did_check — 0; and names the household + the harness dir count when it did

### bad input — 1

- [ ] test_bad_harness_skills_arg_is_a_generic_error — 1; `--harness-skills` pointing at a non-directory

## `agents` — the agent namespace and its gate — 11

Happy path: one `id\tinstalled_name` row per `agents/*.agent.yaml`; `--check` adds
`clean: N agent names unclaimed` plus a `checked:` line per source — including the one it
cannot reach. Skills had a full identity mechanism and agents had none, while
`agents/archiver.agent.yaml` claimed the bare name `archiver` in the user's harness; the
test-only convention of hand-prefixing `tests/golden/PROTOCOL.md`'s profiles
(`aos-archiver`, `aos-steward`) was the evidence the contract was missing rather than unused.
The gate shares `_household_claims` + `_name_collisions` with the skills gate, so the two
cannot drift on what "already claimed" means.

### the naming algorithm — 4

- [ ] test_agent_installed_name_takes_the_capability_prefix — 0; `archiver` under `kb-` → `kb-archiver`, the same computation skills get and the same reason (one flat per-harness namespace)
- [ ] test_agent_prefix_defaults_to_the_capability_id — 0; no `skill_prefix` → `<id>-`, and no `agent_prefix` field exists: §2.2's rule of two, and no in-repo capability wants divergent prefixes
- [ ] test_a_capability_with_no_agents_is_clean — 0; most capabilities ship none, so an absent `agents/` prints nothing and exits 0 — never an error
- [ ] test_agent_json_reports_the_mapping — 0; `--json` carries the capability, the prefix, and ordered `id`→`installed_name`

### the gate says yes — 2

- [ ] test_agent_check_clean_reports_unclaimed — 0; the clean report counts the names it cleared
- [ ] test_agent_check_names_the_source_it_could_not_check — **PIN**; 0; `--harness-agents` enumeration is deferred (a different listing command in each of the five cheat-sheets, for a source no shipped capability collides on) — so the report must say `NO --harness-agents SUPPORTED YET` in as many words. `names.py`'s own rule: a skipped source must never be indistinguishable from an empty one

### exit 17 — 3

- [ ] test_agent_collision_with_another_household_capability — 17; another capability's agent already claims the name, and the report names the owner
- [ ] test_agent_collision_with_a_lockfile_link — 17; a recorded link attributes the name to another install — the second of the two sources this gate reads
- [ ] test_agent_collision_inside_one_capability — 17; `archiver` + `kb-archiver` under `kb-` compute one name ("...in itself"), the agent mirror of the skills case

### name validation, against the INSTALLED name — 2

- [ ] test_over_long_agent_installed_name_rejected — 12; an agent name too long is as fatal as a skill's — the harness writes it as a directory or a filename
- [ ] test_reserved_word_in_agent_installed_name_rejected — 12; `claude`/`anthropic` are reserved in the agent namespace too. `validated_manifest` checked skill names against `name_errors()` and nothing checked agents

## `render` — 13 · name slots — 18

Happy path: `skills/<id>/` lands at `<out>/<installed-name>/`, `name:` rewritten to the
installed name, `metadata.aos.origin` stamped `<cap>@<version>`, bundled `reference/`
carried, `{{mod: …}}` slots untouched.

- [ ] test_render_lands_under_the_installed_name — 0; incl. the origin stamp read as YAML, never as a substring
- [ ] test_render_carries_bundled_assets — 0; the sibling `reference/` travels with the render
- [ ] test_render_preserves_mod_slots — 0; render is mechanical: it never resolves overlay slots
- [ ] test_render_is_idempotent — 0; `--force` twice produces byte-identical output
- [ ] test_render_never_inherits_a_stale_origin_tag — 0; a source carrying somebody else's origin is re-stamped, not trusted
- [ ] test_render_merges_the_stamp_into_an_existing_metadata_block — **PIN**; 0; `metadata` is the Agent Skills spec's **own** extension hatch, so `metadata.<harness>.*` is legitimate sibling data. The old line-based writer appended a top-level key and could not see a sibling at all — the stamp must merge, never clobber
- [ ] test_render_refuses_to_clobber_without_force — 1; and the message names `--force`
- [ ] test_render_destination_that_is_a_file_errors_cleanly — 1; no traceback
- [ ] test_render_destination_that_is_a_symlink_errors_cleanly — 1; a link where the render belongs is someone else's artifact — never `rmtree`d **through**
- [ ] test_render_into_the_packages_own_skills_dir_is_refused — **PIN**; 1; the destructive case, and not a corner one: a capability written by `capability-build`/`capability-import` lives in `personal/capabilities/<id>/`, which is exactly where install and upgrade say to render — so `--out <pkg>/skills` fires on its **first** upgrade. For the entry skill dest == src, `rmtree` runs before `copytree`, and the user's hand-written skill plus its whole `reference/` tree is deleted before the copy dies on the source it just removed. Refuse before touching anything
- [ ] test_render_of_a_non_entry_skill_into_the_package_is_refused_too — **PIN**; 1; the second half of the same defect, which a narrower `dest == src` guard misses: `skills/sort` → `skills/democap-sort` destroys nothing but plants an on-disk skill nothing declares, so every later `manifest`/`skills`/`render` exits 12 and the install can no longer be upgraded or removed
- [ ] test_render_to_the_package_root_is_refused — **PIN**; 1; the mildest case (litter beside `CAPABILITY.md`), kept so the rule stays statable in one clause: `--out` lives outside the package
- [ ] test_render_unknown_skill_errors — 14; an undeclared skill id

## name slots — `{{skill:}}` / `{{agent:}}` at render — 18

The defect this section exists for: an installed name is **computed**
(`<skill_prefix><id>`), so prose that hardcodes one silently points at nothing the moment
the prefix changes. Two probes proved nothing caught it — renaming a `skill_prefix` and
corrupting a hardcoded name both left the lint at **0 errors**. Prose carries a slot, and
an unresolvable one is exit **18**.

### resolution — 7

- [ ] test_slot_resolves_an_own_capability_skill — 0; `{{skill: route}}` → `kb-route`, and no `{{skill:` survives
- [ ] test_agent_slot_takes_the_same_prefix_as_skills — 0; agents land in the same flat namespace, so they reuse the capability's `skill_prefix` — no second manifest field (§2.2's rule of two)
- [ ] test_cross_capability_slot_resolves_within_upstream — 0; `{{skill: kbc/capture}}` at the *target's* prefix, not the referrer's
- [ ] test_cross_capability_slot_resolves_from_personal_into_upstream — **PIN**; 0; the two-root case. The lookup was `cap_dir.parent` — the SIBLING root only — so a capability in `personal/` naming one in `upstream/` failed on a **correct** reference. That is every capability `capability-build` writes
- [ ] test_entry_skill_slot_is_never_double_prefixed — 0; `{{skill: <cap-id>}}` keeps the bare id, the same rule `installed_name` already holds
- [ ] test_slots_in_reference_files_are_resolved_too — 0; depth lives in a sibling `reference/`, so substituting only SKILL.md would miss most prose that names a skill
- [ ] test_mod_slots_still_survive_the_slot_pass — 0; the two halves of replacement are different by design: `{{mod:}}` is left intact by contract, a dangling name slot is a hard failure

### the escape guard — 4

- [ ] test_escaped_skill_slot_renders_as_a_literal — **PIN**; 0; `capability-lifecycle` documents the very syntax it is rendered by, so without an escape, installing it corrupts its own naming reference. An unescaped slot in the same file still resolves — the guard is per-slot, not a per-file mode
- [ ] test_escaped_agent_slot_renders_as_a_literal — 0
- [ ] test_escaped_mod_slot_renders_as_a_literal — 0; one escape rule for **every** slot type, so the rule is one sentence an author can hold
- [ ] test_an_escaped_slot_naming_nothing_is_not_an_error — 0; the point of an example is that it names a placeholder — validating escaped slots would make every documented sample dangling

### exit 18 — 7

- [ ] test_unknown_skill_id_in_a_slot_exits_18 — 18; names the slot **and** what is declared
- [ ] test_unknown_agent_id_in_a_slot_exits_18 — 18
- [ ] test_unknown_capability_in_a_slot_exits_18 — 18
- [ ] test_a_shadowed_capability_in_a_slot_exits_18_naming_both_roots — 18; the install contract says a personal package shadowing an upstream id is reported loudly, never silently preferred — a slot that quietly took `personal/` would resolve against a package the installer never mentioned
- [ ] test_a_mod_only_personal_directory_is_not_a_shadow — 0; the contract's own caveat: `personal/capabilities/<id>/` is the mirrored **overlay** path and exists for every onboarded capability. Only a dir holding a `CAPABILITY.md` is a package, or a shadow fires on every ordinary install
- [ ] test_a_bare_clone_resolves_siblings_not_a_household_above_it — 0; the household is derived by ANCHORING (the ancestor whose `upstream/`/`personal/` the package is inside), never by finding a marker: `.aos/` sits at `~/` on any machine that has ever installed aos, so a marker search would make a bare kit clone resolve references into the user's real `personal/`
- [ ] test_a_failed_slot_pass_leaves_no_partial_render — 18; the copy already landed when the pass runs, and a half-substituted skill reads as complete to the next step (the diff gate, the symlink) — so the failure is total

## the lockfile — `init record rehash verify show list remove` — 21

Happy path: `init` writes `version: 1` + `installs:`; `record` reports
`N artifacts, N links, N schedules`; `verify` prints `clean: N entries verified`.

### `init` — 4

- [ ] test_init_creates_empty_lockfile — 0
- [ ] test_init_creates_aos_dir_on_fresh_clone — 0; `init` is the one verb that may find no `.aos/` — it creates it
- [ ] test_init_over_existing_lockfile_errors — 1; "already exists"
- [ ] test_init_requires_explicit_clone — 15; `init` creates state, so the household must be named (`--home`/`AOS_HOME`) — never discovered from cwd

### `record` — 9

- [ ] test_record_then_show — 0; version, two artifacts with sha256s, a job, a config key
- [ ] test_record_resolves_relative_paths — 0; a relative `--artifact` is stored absolute, so `verify` from a different cwd still passes
- [ ] test_record_env_lines_and_scripts_roundtrip — 0; env var **names** (never values) and scripts
- [ ] test_record_link_and_verify_clean — 0; the link's target is read from the link itself
- [ ] test_source_root_defaults_and_records — 0; defaults to `upstream`, records `personal`
- [ ] test_relative_and_absolute_links_compare_equal — **PIN**; 0; link targets are compared absolute + lexically normalized, deliberately **not** `resolve()`d: the relative spelling of one destination must not read as drift, and neither must a household under a symlinked path
- [ ] test_record_missing_artifact_clean_error — 16; names the path, no traceback
- [ ] test_record_link_on_regular_file_errors — 16; "not a symlink"
- [ ] test_symlink_as_artifact_rejected — 16; hashing through a link would silently record the target's identity — the message points at `--link`

### `rehash` — 2

- [ ] test_rehash_refreshes_only_hashes — 0; artifacts re-hashed, jobs/keys untouched
- [ ] test_rehash_refuses_to_empty_an_entry — **PIN**; 16; when every recorded artifact is gone that is a broken install, not a rehash. Emptying the entry would make the next `verify` report clean — the entry is left intact instead

### `verify` — 4

- [ ] test_verify_clean_and_drift — 0 then 13; a mutated artifact is named
- [ ] test_verify_flags_missing_and_retargeted_link — 13; `MISSING LINK` then `RELINKED`
- [ ] test_verify_flags_dangling_link — 13; the link exists, its target does not
- [ ] test_verify_unknown_capability — 14

### `show` / `list` / `remove` — 2

- [ ] test_show_unknown_capability — 14
- [ ] test_list_and_remove — 0; `list` shows name + version, `remove` drops the entry

## the household — 5

- [ ] test_home_verb_prints_resolved_root — 0 + 15; the resolved root on stdout, exit 15 where none resolves
- [ ] test_discovery_walks_up_from_cwd — 0; `.aos/` found from a nested cwd
- [ ] test_env_override_wins_over_cwd — 0; `$AOS_HOME` beats discovery
- [ ] test_no_clone_found_errors — 15; the message names `.aos`
- [ ] test_explicit_home_without_state_dir_errors — 15; an explicit `--home` with no `.aos/` is an error, not a fresh start (only `init` may create it)

## tool identity — 3

- [ ] test_the_command_is_aos_cap — 0; `--version` prints `aos-cap <version>`, read from `CAPABILITY.md` rather than pinned
- [ ] test_pyproject_version_tracks_the_capability — **PIN**; the comment in `pyproject.toml` says it tracks the capability version and nothing enforced it, so it silently fell a patch behind during the `aos-lock` → `aos-cap` rename (0.3.4 vs 0.3.5), with no `--version` verb to notice
- [ ] test_the_old_command_name_is_gone — `name`/`[project.scripts]` say `aos-cap`; the old name is spelled defensively (`"aos" + "-lock"`) so a `sed` sweep cannot rewrite the assertion into passing against itself

## added by the rewrite — 2

In-process `CliRunner` never resolves `[project.scripts]` and never crosses a process
boundary, so the one thing it structurally cannot prove gets its own subprocess class
(mirroring `test_kb.py`'s `InstalledScriptSmokeTest`).

- [ ] test_the_installed_script_runs_and_reports_its_version — 0; the real `aos-cap` console script
- [ ] test_the_installed_script_completes_a_real_verb_end_to_end — 0; `init` then `list` through a real process
