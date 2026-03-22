# claude-code-skills repo

This repo contains Claude Code skills used across multiple projects.

## Structure

```
skills/
  <skill-name>/
    SKILL.md          # Required — frontmatter + instructions
    scripts/          # Optional — executable helpers
    references/       # Optional — docs loaded on demand
    assets/           # Optional — templates, fonts, etc.
```

Symlinks in `~/.claude/skills/` point into `skills/` here.

## Making skill changes

**Never edit skills directly on `main`.** All changes go through branches.

Branch naming: `skill/<skill-name>/<short-kebab-description>`

Commit format:
```
skill(<skill-name>): <imperative description>

Context: <what session/task revealed this gap>
```

To review a pending skill branch before merging:
```bash
git diff main skill/<skill-name>/<desc>
git log main..skill/<skill-name>/<desc> --oneline
```

## Skill improvement protocol

Claude Code will propose patches to skills during working sessions when it detects a gap or fix.
The flow is always: **propose → you approve → branch + commit → you merge**.

Claude will never commit to main directly. It will never commit without your explicit approval.

## Adding a new skill

1. Create `skills/<new-skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`)
2. Add a symlink: `ln -s ~/Projects/claude-code-skills/skills/<new-skill-name> ~/.claude/skills/<new-skill-name>`
3. Use the `skill-creator` skill for drafting, testing, and iterating
