---
name: synthetic-beta
description: Synthetic test fixture skill beta. Use only for skill-os internal logic tests; never invoke or install in a real project.
allowed-tools: Read, Write, Edit, Bash, Glob
---

# Synthetic Beta

Second skill in the `synthetic-pack` fixture. Tests use this to verify the
inventory generator walks multiple skill directories and that the
scaffolder copies every file under each `skills/<name>/`.
