---
name: synthetic-pdf-reader
description: Synthetic test fixture skill that depends on the synthetic pack. Use only for skill-os chain-install tests.
allowed-tools: Read, Write, Edit, Bash, Glob
---

# Synthetic PDF Reader

Second fixture-pack skill, used to exercise the chain installer.
`synthetic-pdf` profile depends_on `synthetic`, so installing the chain
yields both `synthetic` and `synthetic-pdf` skill bundles in the target.
