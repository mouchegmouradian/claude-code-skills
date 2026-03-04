# Claude Code Skills

A collection of production-ready [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skills that supercharge your development workflow. Each skill teaches Claude deep domain expertise — architecture patterns, best practices, and code generation templates — so you get senior-engineer-quality output from natural language prompts.

## Skills

| Skill | Status | Description | Install |
|-------|--------|-------------|---------|
| [iOS App Builder](skills/ios-app-builder/) | ![Status](https://img.shields.io/badge/status-tested-brightgreen) | Production-quality iOS apps with SwiftUI, Swift Concurrency, SwiftData, and multi-module architecture | [Quick install](#installation) |
| [Android App Builder](skills/android-app-builder/) | ![Status](https://img.shields.io/badge/status-tested-brightgreen) | Production-quality Android apps with Jetpack Compose, Hilt, Room, and multi-module architecture following NowInAndroid patterns | [Quick install](#installation) |
| [Product Requirements Builder](skills/product-requirements-builder/) | ![Status](https://img.shields.io/badge/status-tested-brightgreen) | Structured PRDs and technical RFCs — from problem statement to implementation-ready specs | [Quick install](#installation) |
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

Replace `<skill-name>` with one of: `ios-app-builder`, `android-app-builder`, `product-requirements-builder`, `zetic-mlange`.

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

**Product Requirements Builder**
```
"Help me spec out a fitness tracking app"
"Write an RFC for the authentication system"
```

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
