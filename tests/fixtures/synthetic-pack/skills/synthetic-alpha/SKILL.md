---
name: synthetic-alpha
description: Synthetic test fixture skill alpha. Use only for skill-os internal logic tests; never invoke or install in a real project.
allowed-tools: Read, Write, Edit, Bash, Glob
---

# Synthetic Alpha

This skill is a self-contained test fixture for `skill-os`. It does not
operate on any real project; it exists so the inventory generator, the
scaffolder, the install plan validator, the install / repo-split writer
previews, and the appliers can be exercised end-to-end without depending on
a real pack repo's `skills/` directory.

## What it does (in tests)

- Provides a valid `SKILL.md` with required frontmatter for the validator
- Has a routable name that the synthetic kernel can list
- Is small enough to keep test runs fast
