# Contributing

Thank you for considering contributing to the C2M UE5 Importer!

## Ways to Contribute

- **Bug reports** — Open an issue using the Bug Report template
- **Feature requests** — Open an issue using the Feature Request template
- **Pull requests** — Fix bugs, add features, improve documentation
- **Testing** — Test with different CoD titles and report any game-specific issues

## Development Setup

1. Fork and clone the repository
2. The plugin is pure Python — no build step required
3. Test inside a UE5 project with the Python Editor Script Plugin enabled

## Code Style

- Follow [PEP 8](https://pep8.org/) conventions
- Use type hints on all public functions
- Write docstrings for all modules, classes, and public functions
- Keep lines under 100 characters

## Submitting a Pull Request

1. Create a branch from `main`: `git checkout -b fix/my-fix`
2. Make your changes
3. Update `CHANGELOG.md` under `[Unreleased]`
4. Open a PR against `main` with a clear description of what changed and why

## Reporting Bugs

Please include:
- Unreal Engine version
- CoD game title and version
- The exact error message from the UE5 Output Log
- Whether the issue is with a specific map or all maps

## Code of Conduct

Be respectful and constructive. This is a community project.
