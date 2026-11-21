# Codex log

Judges score "effective use of Codex". AGENTS.md §0.3 rule 8: for every task that changes code, tests, data or prompts,
Codex adds one row to **`docs/codex-log/<git user.name>.md`**, in the same commit as the change.
One file per person, so teammates never conflict on the same file.

Keep it honest: what Codex did, what a person changed, and how the result was checked.

## Template for a new person file

Copy this into `docs/codex-log/<git user.name>.md`:

```markdown
# Codex log: <name>

| Time | Person | Task | Model / effort | Result | How it was checked |
|---|---|---|---|---|---|
```

Example row (format only): `| 10:40 | <name> | Tests for the 85% rule | gpt-6.2-sol / medium | 9 tests pass | ran pytest |`
