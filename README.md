# GREEN

Generation I Green remake project with a modern, data-driven engine profile.

## Evidence first, expansion second

GREEN is expanded before later-generation content is ported, but expansion
decisions must be anchored to the actual Green ROM and save formats.

The verified Japanese source inputs currently cover:

- Pocket Monsters Green Rev 0 ROM;
- Pocket Monsters Green Rev A ROM;
- one independent 32 KiB save snapshot from each revision.

The binaries are not committed. Their hashes and reproducible observations are
stored in `research/` and `analysis/`.

The original Green ROM/save format is a **legacy import/compatibility layer**.
It is not enlarged in place to become the Generation-10-ready runtime format.

See:

- `docs/ROM_SAVE_EVIDENCE.md`
- `docs/EXPANSION_ARCHITECTURE.md`
- `docs/SAVE_SCHEMA.md`
- `config/capacity.json`
- `research/green-baselines.csv`
- `analysis/rom-bank-diff.csv`
- `analysis/save-bank-observations.csv`
- `tools/inspect_green_inputs.py`

Unknown Generation 10 content remains data, not hard-coded assumptions.
