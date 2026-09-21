# GREEN

Generation I Green remake project with a modern, data-driven engine profile.

## First rule: expand before porting content

GREEN must not inherit Generation I's 8-bit content ceilings as project-wide
limits. Before importing maps, scripts, Pokémon data, battle logic, text, or
assets, the project defines an expansion layer that can accept future content
without another structural rewrite.

The current target is **Generation-10-ready architecture**, not hard-coded
Generation 10 content. Unknown future IDs remain data, not engine constants.

See:

- `docs/EXPANSION_ARCHITECTURE.md`
- `docs/SAVE_SCHEMA.md`
- `config/capacity.json`
- `manifests/generation-limits.csv`
- `manifests/expansion-domains.csv`

The original Pocket Monsters Green data will be preserved as a compatibility
baseline while the remake runtime uses the expanded model.
