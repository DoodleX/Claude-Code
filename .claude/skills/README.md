# Project skills

Skills that load automatically in every Claude Code session opened on this repo.
Copied from their upstream repos with `npx skills add`; `evals/` and `agents/` folders were left out.

| Skill | Source | Commit | License |
|-------|--------|--------|---------|
| stop-slop | hardikpandya/stop-slop | 8da1f030185b | MIT (`stop-slop/LICENSE`) |
| copywriting, lead-magnets, emails, events, content-strategy, social | coreyhaines31/marketingskills | f719a8079c69 | MIT (`LICENSE-marketingskills`) |
| why, analyse-problem, cause-and-effect | NeoLabHQ/context-engineering-kit | 23e2428e809d | GPL-3.0 (`LICENSE-context-engineering-kit`) |
| frontend-design | anthropics/skills | 683bc88e56f3 | `frontend-design/LICENSE.txt` |
| remotion-best-practices | remotion-dev/skills | 32b241b97f4e | No license file upstream. Remotion itself is free for individuals and companies of up to 3 people. |

`remotion-best-practices` is a router: it contains the create, captions, render and other Remotion guides inside it.

To update a skill, run `npx skills add <source> -s <skill> -p -y` from the repo root and review the diff.
