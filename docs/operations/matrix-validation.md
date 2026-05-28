# Matrix Validation

`skill-os` is the hub repo, but the real `SKILL.md` files live in sibling pack
repos. Matrix validation therefore has to check both local hub files and the
pack repos visible on disk.

Use the wrapper:

```bash
python3 scripts/validate_matrix.py --pack-search-path <parent-of-cloned-packs>
```

The wrapper is read-only. It never clones repos, checks out pinned commits, or
writes into sibling packs. It runs:

- `python3 -m unittest discover tests`
- `python3 scripts/export_skill_kernel_adapters.py --runtime all --check`
- `uv run scripts/validate_skill_taxonomy.py` with the same pack paths
- `python3 scripts/verify_pack_pins.py --json` with the same pack paths

## Non-Canonical Pack Paths

If a local clone does not use the canonical repo directory name, pass an
override. The name can be either the repo name or the profile name:

```bash
python3 scripts/validate_matrix.py \
  --pack-search-path /Users/jieke/Projects \
  --pack ml-research=/private/tmp/ml-research-skills
```

Internally, `ml-research` is normalized to `ml-research-skills` so the same
override works for taxonomy validation and pinned-commit verification.

## JSON Report

For automation:

```bash
python3 scripts/validate_matrix.py \
  --pack-search-path <parent-of-cloned-packs> \
  --json
```

The report includes:

- `pack_paths`: each expected pack repo, where it was found, and whether it is
  present
- `steps`: command, exit code, stdout, and stderr for each check
- `summary`: counts of passed, failed, and skipped checks

## When To Run

Run the wrapper after:

- editing `profiles/profile-index.yaml`
- adding or removing pack dependencies
- changing kernel examples or install contracts
- changing chain installer behavior
- refreshing sibling-pack pinned commits
- preparing a public release or milestone tag

If a pack pin mismatch appears, inspect the sibling pack manually and update
`profiles/profile-index.yaml` only after deciding that the newer pack HEAD is
the intended matrix state. The verifier deliberately does not mutate pack repos.
