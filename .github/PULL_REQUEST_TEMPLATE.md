## Type of contribution

- [ ] New skill (`skills/<name>/`)
- [ ] Change to an existing skill
- [ ] Repo tooling / CI / docs
- [ ] Skill deprecation or removal

## Skill name

<!-- for skill changes: which skill, and what changed -->

## Summary

<!-- what does this change do, and why -->

## Validation evidence (required for skill changes)

At least one of the following — check what applies and describe below:

- [ ] Ran the skill's workflow with realistic inputs (what did you run, what happened?)
- [ ] A peer ran it and confirmed in this PR thread
- [ ] Checked-in evals (`evals/evals.json`) with concrete assertions
- [ ] Explicit test steps a reviewer can follow (below)

## Checklist

- [ ] `make lint` passes locally (validator, index check, eval check, tests)
- [ ] README index regenerated with `make index` (if adding/renaming/removing a skill)
- [ ] CODEOWNERS rule added for new skills (`skills/<name>/ @<owner> @eformat @sabre1041 @hultzj`)
- [ ] `metadata.version` bumped appropriately (patch/minor/major)
- [ ] `allowed-tools` scoped to exactly what the skill calls (or omitted deliberately)
- [ ] Human-approval gate stated in the body for anything writing to external systems
- [ ] No secrets, internal hostnames, customer data, or `/home/<user>/` paths
- [ ] Provenance stated for ported skills (source repo + license)

## Test steps

<!-- how a reviewer verifies this -->
