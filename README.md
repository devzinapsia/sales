# Sales
Zinapsia sales-related submodules for Odoo.

## Development setup

This repo ships a versioned git hook that auto-bumps the last version
segment of any `__manifest__.py` staged in a commit (e.g. `19.0.1.0.3` ->
`19.0.1.0.4`), so the Apps version always reflects that a real change was
made. Enable it once per machine:

```bash
git config core.hooksPath .githooks
```
