# RFC-001: Project name

**Status:** open · **Decides:** the project/repo/CLI name (replaces the `aos` placeholder)

## Question

What do we call this thing? The name becomes the repo, the CLI command, the config paths, and the noun in every conversation. The *concept* name is already firm (ARCHITECTURE §8): the unit is a **capability**; the project name should not collide with "skill", "plugin", "recipe", or "agent" — all reserved by the ecosystem.

## Candidates

From the group and beyond — add yours; names are fun and easy to collaborate around:

| Name | For | Against |
|---|---|---|
| `aos` (agent operator system) | Short CLI, current placeholder | Opaque; collides with AOSP associations |
| **`cos-kit` / COS Kit** | Chief-of-staff, the actual product identity; short CLI (`cos install …`) | COS means nothing to outsiders until told |
| **`battery-kit` / Battery Kit** | *The* metaphor — "harnesses are batteries-not-included"; instantly explains itself | Battery ≠ agent-anything without the tagline |
| `batteries` | The boldest version of the same (`batteries install gtd-capture` reads great) | Generic; hard to search |
| **`harness-kit`** | Names where it plugs in | Sounds like it *is* a harness, which it isn't |
| Harness framework / Agent framework / COS framework | Descriptive, serious | "Framework" is the most overloaded word in software; zero personality |
| `capkit` | Says what it is (capability kit) | A bit product-y |
| `opkit` | Keeps the "operator layer" identity | "op" reads as DevOps |
| `agent-commons` | Names the politics (a commons) | Long CLI; no verb energy |
| `operator-os` / `co-os` / `capability-os` / `harness-plus` / `agent-kit` | earlier candidates | "OS" overpromises; the rest are flat |
| `second-stack` | The "second brain" heritage, one level down | Cute, maybe too cute |
| `commonos` | commons + OS pun | Pun taxes every reader |

## Recommendation

Pick for the CLI experience first (`X install personal-trainer` should read well), the mission second. Strongest triangle: **`battery-kit`** (metaphor), **`cos-kit`** (identity), **`agent-commons`** (politics). A workable split: repo/brand = one of the first two, CLI = a 3-4 letter contraction of it.

## Process

Propose/argue in comments; maintainer calls it after the group weighs in. **Auto-accept:** if no objection to the recommendation within the RFC-003 deadline window, the recommendation stands.
