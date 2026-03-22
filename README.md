# Claude Code Skills

A collection of production-ready [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills that supercharge your development workflow. Each skill teaches Claude deep domain expertise — architecture patterns, best practices, and code generation templates — so you get senior-engineer-quality output from natural language prompts.

## Skills

| Skill | Status | Description | Install |
|-------|--------|-------------|---------|
| [iOS App Builder](skills/ios-app-builder/) | ![Status](https://img.shields.io/badge/status-tested-brightgreen) | Production-quality iOS apps with SwiftUI, Swift Concurrency, SwiftData, and multi-module architecture | [Quick install](#installation) |
| [Android App Builder](skills/android-app-builder/) | ![Status](https://img.shields.io/badge/status-tested-brightgreen) | Production-quality Android apps with Jetpack Compose, Hilt, Room, and multi-module architecture following NowInAndroid patterns | [Quick install](#installation) |
| [Product Requirements Builder](skills/product-requirements-builder/) | ![Status](https://img.shields.io/badge/status-tested-brightgreen) | Structured PRDs and technical RFCs — from problem statement to implementation-ready specs | [Quick install](#installation) |
| [Orchestrator](skills/orchestrator/) | ![Status](https://img.shields.io/badge/status-new-blue) | Multi-agent coordination for large implementations — phases sub-agents by RFC, manages parallelization, and verifies integration between phases | [Quick install](#installation) |
| [Flutter App Builder](skills/flutter-app-builder/) | ![Status](https://img.shields.io/badge/status-WIP-orange) | Production-quality Flutter apps with BLoC/Cubit, go_router, and complexity-aware architecture (Tier 1 simple / Tier 2 production) | [Quick install](#installation) |
| [Skill Improvement](skills/skill-improvement/) | ![Status](https://img.shields.io/badge/status-tested-brightgreen) | Automatically detects skill gaps during sessions and proposes targeted patches — keeping skills accurate without manual maintenance | [Quick install](#installation) |
| [ZETIC MLange SDK](skills/zetic-mlange/) | ![Status](https://img.shields.io/badge/status-untested-yellow) | On-device AI inference for Android & iOS — general models, LLMs, and HuggingFace integration with NPU acceleration | [Quick install](#installation) |

## What Are Claude Code Skills?

Skills are markdown instruction files that live in `~/.claude/skills/`. When activated, they give Claude Code deep context about a specific domain — architecture patterns, coding conventions, reference implementations — so it can generate code that follows best practices out of the box.

Think of them as "expert knowledge packs" for Claude.

## Installation

### Install all skills (copy)

```bash
git clone https://github.com/mouchegmouradian/claude-code-skills.git
cp -r claude-code-skills/skills/* ~/.claude/skills/
```

### Install a single skill (copy)

```bash
git clone https://github.com/mouchegmouradian/claude-code-skills.git
cp -r claude-code-skills/skills/<skill-name> ~/.claude/skills/
```

Replace `<skill-name>` with one of: `ios-app-builder`, `android-app-builder`, `flutter-app-builder`, `product-requirements-builder`, `orchestrator`, `skill-improvement`, `zetic-mlange`.

### Install with symlinks (auto-update)

Symlink the skills so they stay up to date — just `git pull` to get the latest changes.

```bash
git clone https://github.com/mouchegmouradian/claude-code-skills.git
ln -s "$(pwd)/claude-code-skills/skills/"* ~/.claude/skills/
```

Or a single skill:

```bash
ln -s "$(pwd)/claude-code-skills/skills/<skill-name>" ~/.claude/skills/
```

### Verify installation

```bash
ls -la ~/.claude/skills/
```

You should see the skill folder(s) (or symlinks pointing to them). Claude Code will automatically detect and load them in your next session.

## Usage

Once installed, skills activate automatically based on context. Just ask Claude naturally:

**iOS App Builder**
```
"Create a new SwiftUI screen for user settings with offline support"
"Build a networking layer using async/await and actors"
```

**Android App Builder**
```
"Create a new feature module for user profile with Compose UI"
"Set up Room database with offline-first repository pattern"
```

**Flutter App Builder** *(WIP)*
```
"Create a new Flutter app for tracking habits"
"Add a user profile feature to my Flutter app"
"Set up go_router with type-safe routes"
```

**Product Requirements Builder**
```
"Help me spec out a fitness tracking app"
"Write an RFC for the authentication system"
```

**Orchestrator**
```
"Implement all the RFCs in the PRD/ folder"
"Orchestrate the full app build across all feature areas"
"Spawn sub-agents to build each RFC in parallel"
```

**Skill Improvement**
```
"The skill missed this pattern — add it"
"Update the skill based on what we just fixed"
```
*(Also triggers automatically at the end of any session where a skill was used and a gap was found)*

**ZETIC MLange SDK**
```
"Integrate ZeticMLangeModel for on-device object detection"
"Add LLM chat with streaming tokens using ZeticMLangeLLMModel"
```

## Contributing

Contributions are welcome! If you'd like to improve an existing skill or add a new one:

1. Fork the repository
2. Create a feature branch (`git checkout -b skill/my-new-skill`)
3. Follow the existing skill structure (see any skill folder for reference)
4. Submit a pull request

### Skill structure

```
skills/your-skill-name/
├── SKILL.md            # Main skill definition (required)
├── references/         # Domain knowledge and patterns
├── templates/          # Code generation templates (optional)
├── scripts/            # Helper scripts (optional)
└── README.md           # Skill-specific documentation
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Links

- [Live Showcase](https://mouchegmouradian.github.io/claude-code-skills/) — browse skills with one-click install commands
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)
- [Claude Code Skills Guide](https://docs.anthropic.com/en/docs/claude-code/skills)
