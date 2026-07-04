# Contributing to invAIriant

Single maintainer: **[@mindicator](https://github.com/mindicator)**.
Documentation authorship is credited as **mindicator & silicon bags quartet**.

This project practices what it audits, so its contribution rules are short and
enforced by the framework's own checks.

## Definition of done for a change

- **Self-validation passes.** `scripts/validate_framework.py` is green: all
  JSON schemas parse, example configs validate against
  `schemas/invairiant.config.schema.json`, the example findings validate
  against `schemas/finding.schema.json`, and every lens file carries the
  required sections. CI runs this as
  [`.github/workflows/validate.yml`](.github/workflows/validate.yml).
- **Lens files keep the canonical structure.** New or edited lenses preserve
  the section order and the verbatim 0–10 scoring rubric (see any file under
  [`lenses/`](lenses/) and the writing guide in
  [docs/lens-taxonomy.md](docs/lens-taxonomy.md)).
- **The protocol's own rules hold in the text.** No lens or template weakens
  "no evidence, no finding," the anti-averaging rule, or the
  observation/finding separation.

## Releasing

The rule is mechanical, not a thing to remember: **push → wait for CI green on
that commit → only then tag and release.** It is enforced by a local pre-push
hook that refuses to push a **tag** whose commit does not have green CI (branch
pushes pass through — CI runs after them). Install it once per clone:

```bash
bash scripts/install-hooks.sh      # installs .git/hooks/pre-push
```

The check itself lives in [`scripts/release-gate.sh`](scripts/release-gate.sh)
(runnable by hand: `scripts/release-gate.sh v0.2.3`) and fails closed — no `gh`,
no CI runs yet, or any non-`success` check blocks the release. Last-resort
override: `git push --no-verify`.

**Publishing to PyPI** (build from the tag, upload the immutable version) is a
separate maintainer step — see [docs/publishing.md](docs/publishing.md).

## Scope of changes

- **New lenses** go in the right pack with a kebab-case id; cross-listed
  lenses get a stub, never a fork ([docs/lens-taxonomy.md](docs/lens-taxonomy.md)).
- **Schema changes** are contracts — bump thoughtfully; the schemas are the
  stable interface other tooling depends on.
- **Domain-specific material** stays out of the generic core; domain
  judgment belongs in [`lenses/domain/`](lenses/domain/).

## Reporting issues

Open a GitHub issue with concrete evidence — the same standard the protocol
sets for findings. "This feels off" is an observation; a file/line, a failing
check, or a doc/code contradiction is a report that can be acted on.

## License

By contributing you agree that your contributions are licensed under
[Apache-2.0](LICENSE).
